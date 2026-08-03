from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import Cycle, JoinRequest, Membership, Pool, User
from app.schemas import (
    JoinRequestOut,
    MemberOut,
    PoolCreate,
    PoolDetailOut,
    PoolJoin,
    PoolOut,
    PoolPublicOut,
)
from app.services.trust_score import compute_trust_score

router = APIRouter(prefix="/pools", tags=["pools"])


def _pool_out(pool: Pool) -> PoolOut:
    return PoolOut(
        id=pool.id,
        name=pool.name,
        contribution_amount=pool.contribution_amount,
        member_cap=pool.member_cap,
        invite_code=pool.invite_code,
        current_cycle_number=pool.current_cycle_number,
        status=pool.status,
        member_count=len(pool.memberships),
    )


def _member_out(m: Membership) -> MemberOut:
    return MemberOut(
        membership_id=m.id,
        user_id=m.user_id,
        name=m.user.name,
        is_head=m.is_head,
        has_won=m.has_won,
        trust_score=compute_trust_score(m.on_time_count, m.total_contributions_count),
    )


def _get_membership(db: Session, pool_id: int, user_id: int) -> Membership | None:
    return db.query(Membership).filter(Membership.pool_id == pool_id, Membership.user_id == user_id).first()


def _require_head(db: Session, pool_id: int, user: User) -> Membership:
    membership = _get_membership(db, pool_id, user.id)
    if membership is None or not membership.is_head:
        raise HTTPException(status_code=403, detail="Only the pool head can do this")
    return membership


@router.post("", response_model=PoolOut)
def create_pool(payload: PoolCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    pool = Pool(
        name=payload.name,
        contribution_amount=payload.contribution_amount,
        member_cap=payload.member_cap,
        created_by=user.id,
    )
    db.add(pool)
    db.flush()

    membership = Membership(pool_id=pool.id, user_id=user.id, is_head=True)
    db.add(membership)
    db.flush()

    db.add(Cycle(pool_id=pool.id, cycle_number=1, status="collecting"))
    db.commit()
    db.refresh(pool)
    return _pool_out(pool)


@router.post("/join", response_model=PoolOut)
def join_pool(payload: PoolJoin, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    pool = db.query(Pool).filter(Pool.invite_code == payload.invite_code).first()
    if pool is None:
        raise HTTPException(status_code=404, detail="Invalid invite code")
    if pool.status != "active":
        raise HTTPException(status_code=400, detail="Pool is no longer accepting members")
    if len(pool.memberships) >= pool.member_cap:
        raise HTTPException(status_code=400, detail="Pool is full")
    if _get_membership(db, pool.id, user.id) is not None:
        raise HTTPException(status_code=400, detail="Already a member of this pool")

    db.add(Membership(pool_id=pool.id, user_id=user.id))
    db.commit()
    db.refresh(pool)
    return _pool_out(pool)


@router.get("", response_model=list[PoolOut])
def list_my_pools(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    memberships = db.query(Membership).filter(Membership.user_id == user.id).all()
    return [_pool_out(m.pool) for m in memberships]


@router.get("/discover", response_model=list[PoolPublicOut])
def discover_pools(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    pools = db.query(Pool).filter(Pool.status == "active").all()
    my_pending = {
        r.pool_id
        for r in db.query(JoinRequest).filter(JoinRequest.user_id == user.id, JoinRequest.status == "pending").all()
    }
    out = []
    for pool in pools:
        head = next((m for m in pool.memberships if m.is_head), None)
        out.append(
            PoolPublicOut(
                id=pool.id,
                name=pool.name,
                contribution_amount=pool.contribution_amount,
                member_cap=pool.member_cap,
                current_cycle_number=pool.current_cycle_number,
                status=pool.status,
                member_count=len(pool.memberships),
                head_name=head.user.name if head else "-",
                is_member=any(m.user_id == user.id for m in pool.memberships),
                has_pending_request=pool.id in my_pending,
            )
        )
    return out


@router.post("/{pool_id}/join-requests", response_model=JoinRequestOut)
def request_to_join(pool_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    pool = db.get(Pool, pool_id)
    if pool is None:
        raise HTTPException(status_code=404, detail="Pool not found")
    if pool.status != "active":
        raise HTTPException(status_code=400, detail="Pool is no longer accepting members")
    if len(pool.memberships) >= pool.member_cap:
        raise HTTPException(status_code=400, detail="Pool is full")
    if _get_membership(db, pool.id, user.id) is not None:
        raise HTTPException(status_code=400, detail="Already a member of this pool")
    existing = (
        db.query(JoinRequest)
        .filter(JoinRequest.pool_id == pool.id, JoinRequest.user_id == user.id, JoinRequest.status == "pending")
        .first()
    )
    if existing is not None:
        raise HTTPException(status_code=400, detail="You already have a pending request for this pool")

    req = JoinRequest(pool_id=pool.id, user_id=user.id)
    db.add(req)
    db.commit()
    db.refresh(req)
    return JoinRequestOut(id=req.id, pool_id=req.pool_id, user_id=req.user_id, requester_name=user.name, status=req.status)


@router.get("/{pool_id}/join-requests", response_model=list[JoinRequestOut])
def list_join_requests(pool_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _require_head(db, pool_id, user)
    requests = (
        db.query(JoinRequest)
        .filter(JoinRequest.pool_id == pool_id, JoinRequest.status == "pending")
        .order_by(JoinRequest.created_at)
        .all()
    )
    return [
        JoinRequestOut(id=r.id, pool_id=r.pool_id, user_id=r.user_id, requester_name=r.user.name, status=r.status)
        for r in requests
    ]


@router.post("/{pool_id}/join-requests/{request_id}/approve", response_model=JoinRequestOut)
def approve_join_request(
    pool_id: int, request_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    _require_head(db, pool_id, user)
    req = db.get(JoinRequest, request_id)
    if req is None or req.pool_id != pool_id:
        raise HTTPException(status_code=404, detail="Join request not found")
    if req.status != "pending":
        raise HTTPException(status_code=400, detail="Request already resolved")

    pool = db.get(Pool, pool_id)
    if len(pool.memberships) >= pool.member_cap:
        raise HTTPException(status_code=400, detail="Pool is full")

    db.add(Membership(pool_id=pool_id, user_id=req.user_id))
    req.status = "approved"
    db.commit()
    db.refresh(req)
    return JoinRequestOut(
        id=req.id, pool_id=req.pool_id, user_id=req.user_id, requester_name=req.user.name, status=req.status
    )


@router.post("/{pool_id}/join-requests/{request_id}/reject", response_model=JoinRequestOut)
def reject_join_request(
    pool_id: int, request_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    _require_head(db, pool_id, user)
    req = db.get(JoinRequest, request_id)
    if req is None or req.pool_id != pool_id:
        raise HTTPException(status_code=404, detail="Join request not found")
    if req.status != "pending":
        raise HTTPException(status_code=400, detail="Request already resolved")

    req.status = "rejected"
    db.commit()
    db.refresh(req)
    return JoinRequestOut(
        id=req.id, pool_id=req.pool_id, user_id=req.user_id, requester_name=req.user.name, status=req.status
    )


@router.get("/{pool_id}", response_model=PoolDetailOut)
def get_pool(pool_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    pool = db.get(Pool, pool_id)
    if pool is None:
        raise HTTPException(status_code=404, detail="Pool not found")
    is_member = any(m.user_id == user.id for m in pool.memberships)
    if not is_member:
        raise HTTPException(status_code=403, detail="Not a member of this pool")

    base = _pool_out(pool)
    return PoolDetailOut(**base.model_dump(), members=[_member_out(m) for m in pool.memberships])
