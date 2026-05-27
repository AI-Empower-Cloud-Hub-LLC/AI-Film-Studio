"""
MongoDB persistence for pipeline history, generated content, and analytics.

Uses motor (async MongoDB driver). Falls back to in-memory storage if
MongoDB is not configured or unavailable.
"""
import time
import logging
from typing import Dict, Any, List, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

_client = None
_db = None


def _get_db():
    """Lazy-init MongoDB connection."""
    global _client, _db
    if _db is not None:
        return _db
    url = getattr(settings, "MONGODB_URL", "")
    if not url:
        return None
    try:
        import motor.motor_asyncio  # type: ignore[import-untyped]
        _client = motor.motor_asyncio.AsyncIOMotorClient(url, serverSelectionTimeoutMS=3000)
        db_name = getattr(settings, "MONGODB_DB_NAME", "ai_film_studio")
        _db = _client[db_name]
        logger.info("Connected to MongoDB: %s", db_name)
        return _db
    except Exception as exc:
        logger.warning("MongoDB unavailable: %s — using in-memory fallback", exc)
        return None


class MongoStore:
    """Persistent storage for pipeline runs and generated content."""

    def __init__(self):
        self._memory_runs: List[Dict[str, Any]] = []

    async def save_run(self, run: Dict[str, Any]) -> str:
        """Save a pipeline run record. Returns the run ID."""
        run.setdefault("timestamp", time.time())
        run.setdefault("_id", f"run_{int(run['timestamp'] * 1000)}")

        db = _get_db()
        if db is not None:
            try:
                coll = db["pipeline_runs"]
                await coll.insert_one(run)
                logger.info("Saved pipeline run to MongoDB: %s", run["_id"])
                return run["_id"]
            except Exception as exc:
                logger.warning("MongoDB save failed: %s — using memory", exc)

        self._memory_runs.append(run)
        return run["_id"]

    async def get_runs(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent pipeline runs (newest first)."""
        db = _get_db()
        if db is not None:
            try:
                coll = db["pipeline_runs"]
                cursor = coll.find().sort("timestamp", -1).limit(limit)
                runs = []
                async for doc in cursor:
                    doc.pop("_id", None)
                    runs.append(doc)
                return runs
            except Exception as exc:
                logger.warning("MongoDB query failed: %s — using memory", exc)

        return list(reversed(self._memory_runs[-limit:]))

    async def save_generated_content(
        self, project_id: str, scene_number: int, content_type: str, data: Dict[str, Any]
    ) -> None:
        """Save generated media (video/audio) metadata."""
        record = {
            "project_id": project_id,
            "scene_number": scene_number,
            "content_type": content_type,
            "timestamp": time.time(),
            **data,
        }
        db = _get_db()
        if db is not None:
            try:
                await db["generated_content"].insert_one(record)
                return
            except Exception as exc:
                logger.warning("MongoDB content save failed: %s", exc)

    async def get_generated_content(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all generated content for a project."""
        db = _get_db()
        if db is not None:
            try:
                cursor = db["generated_content"].find(
                    {"project_id": project_id}
                ).sort("scene_number", 1)
                results = []
                async for doc in cursor:
                    doc.pop("_id", None)
                    results.append(doc)
                return results
            except Exception as exc:
                logger.warning("MongoDB content query failed: %s", exc)
        return []

    async def get_analytics(self) -> Dict[str, Any]:
        """Get pipeline analytics (total runs, avg timings, etc.)."""
        db = _get_db()
        if db is not None:
            try:
                coll = db["pipeline_runs"]
                total = await coll.count_documents({})
                success = await coll.count_documents({"status": "success"})
                return {
                    "total_runs": total,
                    "successful_runs": success,
                    "failure_rate": round(1 - success / max(total, 1), 2),
                    "storage": "mongodb",
                }
            except Exception as exc:
                logger.warning("MongoDB analytics failed: %s", exc)

        return {
            "total_runs": len(self._memory_runs),
            "successful_runs": sum(1 for r in self._memory_runs if r.get("status") == "success"),
            "storage": "memory",
        }


mongo_store = MongoStore()
