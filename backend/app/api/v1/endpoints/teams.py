"""Team collaboration endpoints — CRUD teams, invite members, share projects."""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel as PydanticModel, EmailStr, Field
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.team import Team, TeamMember, TeamInvite, ProjectShare, TeamRole, InviteStatus

router = APIRouter()


class CreateTeamReq(PydanticModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class InviteMemberReq(PydanticModel):
    email: EmailStr
    role: TeamRole = TeamRole.viewer


class ShareProjectReq(PydanticModel):
    project_id: str


class TeamOut(PydanticModel):
    id: str
    name: str
    description: Optional[str]
    owner_id: str
    member_count: int
    created_at: str


class MemberOut(PydanticModel):
    id: str
    user_id: str
    email: str
    full_name: str
    role: str
    joined_at: str


@router.get("/")
def list_teams(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    memberships = db.query(TeamMember).filter(TeamMember.user_id == user.id).all()
    team_ids = [m.team_id for m in memberships]
    teams = db.query(Team).filter(Team.id.in_(team_ids)).all() if team_ids else []
    return [
        TeamOut(
            id=t.id, name=t.name, description=t.description, owner_id=t.owner_id,
            member_count=len(t.members), created_at=t.created_at.isoformat(),
        )
        for t in teams
    ]


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_team(body: CreateTeamReq, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    team = Team(id=str(uuid.uuid4()), name=body.name, description=body.description, owner_id=user.id)
    db.add(team)
    member = TeamMember(id=str(uuid.uuid4()), team_id=team.id, user_id=user.id, role=TeamRole.owner)
    db.add(member)
    db.commit()
    return {"id": team.id, "name": team.name, "message": "Team created"}


@router.get("/{team_id}")
def get_team(team_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    membership = db.query(TeamMember).filter(TeamMember.team_id == team_id, TeamMember.user_id == user.id).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a team member")
    members = db.query(TeamMember).filter(TeamMember.team_id == team_id).all()
    member_list = []
    for m in members:
        u = db.query(User).filter(User.id == m.user_id).first()
        if u:
            member_list.append(MemberOut(
                id=m.id, user_id=m.user_id, email=u.email,
                full_name=u.full_name, role=m.role.value, joined_at=m.joined_at.isoformat(),
            ))
    shares = db.query(ProjectShare).filter(ProjectShare.team_id == team_id).all()
    return {
        "id": team.id, "name": team.name, "description": team.description,
        "owner_id": team.owner_id, "members": member_list,
        "shared_projects": [{"id": s.id, "project_id": s.project_id} for s in shares],
        "created_at": team.created_at.isoformat(),
    }


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(team_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    team = db.query(Team).filter(Team.id == team_id, Team.owner_id == user.id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found or not owner")
    db.delete(team)
    db.commit()


@router.post("/{team_id}/invite")
def invite_member(team_id: str, body: InviteMemberReq, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    membership = db.query(TeamMember).filter(
        TeamMember.team_id == team_id, TeamMember.user_id == user.id,
        TeamMember.role.in_([TeamRole.owner, TeamRole.admin]),
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Must be team owner or admin to invite")
    existing = db.query(TeamInvite).filter(
        TeamInvite.team_id == team_id, TeamInvite.invitee_email == body.email,
        TeamInvite.status == InviteStatus.pending,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Invite already pending")
    invite = TeamInvite(
        id=str(uuid.uuid4()), team_id=team_id, inviter_id=user.id,
        invitee_email=body.email, role=body.role,
    )
    db.add(invite)
    db.commit()
    return {"id": invite.id, "message": f"Invite sent to {body.email}"}


@router.get("/{team_id}/invites")
def list_invites(team_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    membership = db.query(TeamMember).filter(TeamMember.team_id == team_id, TeamMember.user_id == user.id).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a team member")
    invites = db.query(TeamInvite).filter(TeamInvite.team_id == team_id).all()
    return [{"id": i.id, "email": i.invitee_email, "role": i.role.value, "status": i.status.value} for i in invites]


@router.post("/invites/{invite_id}/accept")
def accept_invite(invite_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    invite = db.query(TeamInvite).filter(TeamInvite.id == invite_id, TeamInvite.invitee_email == user.email).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")
    if invite.status != InviteStatus.pending:
        raise HTTPException(status_code=400, detail="Invite already responded")
    invite.status = InviteStatus.accepted
    member = TeamMember(id=str(uuid.uuid4()), team_id=invite.team_id, user_id=user.id, role=invite.role)
    db.add(member)
    db.commit()
    return {"message": "Joined team"}


@router.post("/{team_id}/share")
def share_project(team_id: str, body: ShareProjectReq, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    membership = db.query(TeamMember).filter(
        TeamMember.team_id == team_id, TeamMember.user_id == user.id,
        TeamMember.role.in_([TeamRole.owner, TeamRole.admin, TeamRole.editor]),
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Must be owner, admin, or editor to share")
    existing = db.query(ProjectShare).filter(
        ProjectShare.team_id == team_id, ProjectShare.project_id == body.project_id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Project already shared with this team")
    share = ProjectShare(
        id=str(uuid.uuid4()), project_id=body.project_id,
        team_id=team_id, shared_by=user.id,
    )
    db.add(share)
    db.commit()
    return {"id": share.id, "message": "Project shared with team"}


@router.delete("/{team_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(team_id: str, member_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    membership = db.query(TeamMember).filter(
        TeamMember.team_id == team_id, TeamMember.user_id == user.id,
        TeamMember.role.in_([TeamRole.owner, TeamRole.admin]),
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Must be team owner or admin")
    target = db.query(TeamMember).filter(TeamMember.id == member_id, TeamMember.team_id == team_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Member not found")
    if target.role == TeamRole.owner:
        raise HTTPException(status_code=400, detail="Cannot remove team owner")
    db.delete(target)
    db.commit()
