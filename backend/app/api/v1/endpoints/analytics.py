"""Analytics endpoints — usage stats, trends, and event tracking."""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.project import Project, Scene, ProjectStatus
from app.models.analytics import UsageEvent, DailyStat

router = APIRouter()


@router.get("/overview")
def analytics_overview(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    total_users = db.query(func.count(User.id)).scalar() or 0
    total_projects = db.query(func.count(Project.id)).scalar() or 0
    completed_projects = db.query(func.count(Project.id)).filter(Project.status == ProjectStatus.completed).scalar() or 0
    total_scenes = db.query(func.count(Scene.id)).scalar() or 0

    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_projects = db.query(func.count(Project.id)).filter(Project.created_at >= seven_days_ago).scalar() or 0
    recent_users = db.query(func.count(User.id)).filter(User.created_at >= seven_days_ago).scalar() or 0

    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    monthly_projects = db.query(func.count(Project.id)).filter(Project.created_at >= thirty_days_ago).scalar() or 0

    return {
        "total_users": total_users,
        "total_projects": total_projects,
        "completed_projects": completed_projects,
        "total_scenes": total_scenes,
        "recent_7d": {"projects": recent_projects, "users": recent_users},
        "monthly_projects": monthly_projects,
        "completion_rate": round(completed_projects / max(total_projects, 1) * 100, 1),
        "avg_scenes_per_film": round(total_scenes / max(completed_projects, 1), 1),
    }


@router.get("/trends")
def analytics_trends(days: int = 30, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    start_date = datetime.utcnow() - timedelta(days=days)
    daily_data = []
    for i in range(days):
        day = start_date + timedelta(days=i)
        day_str = day.strftime("%Y-%m-%d")
        next_day = day + timedelta(days=1)

        films = db.query(func.count(Project.id)).filter(
            Project.created_at >= day, Project.created_at < next_day,
        ).scalar() or 0
        users = db.query(func.count(User.id)).filter(
            User.created_at >= day, User.created_at < next_day,
        ).scalar() or 0

        daily_data.append({"date": day_str, "films": films, "users": users})

    return {"days": days, "data": daily_data}


@router.get("/top-styles")
def top_styles(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    styles = db.query(Project.style, func.count(Project.id).label("count")).group_by(Project.style).order_by(func.count(Project.id).desc()).all()
    return [{"style": s[0], "count": s[1]} for s in styles]


@router.get("/user-activity")
def user_activity(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    users = db.query(User).order_by(User.created_at.desc()).limit(50).all()
    result = []
    for u in users:
        project_count = db.query(func.count(Project.id)).scalar() or 0
        result.append({
            "id": u.id, "email": u.email, "full_name": u.full_name,
            "projects": project_count, "joined": u.created_at.isoformat(),
            "is_admin": u.is_admin,
        })
    return result


@router.post("/track")
def track_event(event_type: str, project_id: str = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    import uuid
    event = UsageEvent(
        id=str(uuid.uuid4()), user_id=user.id, event_type=event_type,
        project_id=project_id,
    )
    db.add(event)
    db.commit()
    return {"status": "tracked"}
