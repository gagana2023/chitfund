from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import Bid as BidModel
from app.models import Cycle, LedgerEntry, Membership, Pool, User
from app.schemas import BidCreate, BidOut, ContributeRequest, CycleOut, LedgerEntryOut
from app.services.bidding_engine import Bid as EngineBid
from app.services.bidding_engine import resolve_cycle_bids

router = APIRouter(prefix="/pools/{pool_id}", tags=["cycles"])


def _get_pool_and_membership(db: Session, pool_id: int, user: User) -> tuple[Pool, Membership]:
    pool = db.get(Pool, pool_id)
    if pool is None:
        raise HTTPException(status_code=404, detail="Pool not found")
    membership = db.query(Membership).filter(Membership.pool_id == pool_id, Membership.user_id == user.id).first()
    if membership is None:
        raise HTTPException(status_code=403, detail="Not a member of this pool")
    return pool, membership


def _current_cycle(db: Session, pool: Pool) -> Cycle:
    cycle = (
        db.query(Cycle)
        .filter(Cycle.pool_id == pool.id, Cycle.cycle_number == pool.current_cycle_number)
        .first()
    )
    if cycle is None:
        raise HTTPException(status_code=404, detail="No active cycle")
    return cycle


def _cycle_out(cycle: Cycle, db: Session) -> CycleOut:
    winner_name = None
    if cycle.winner_membership_id:
        winner = db.get(Membership, cycle.winner_membership_id)
        winner_name = winner.user.name if winner else None
    return CycleOut(
        id=cycle.id,
        cycle_number=cycle.cycle_number,
        status=cycle.status,
        winner_membership_id=cycle.winner_membership_id,
        winner_name=winner_name,
        winning_bid_amount=cycle.winning_bid_amount,
        dividend_per_member=cycle.dividend_per_member,
    )


@router.get("/cycles/current", response_model=CycleOut)
def get_current_cycle(pool_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    pool, _ = _get_pool_and_membership(db, pool_id, user)
    cycle = _current_cycle(db, pool)
    return _cycle_out(cycle, db)


@router.post("/contribute", response_model=CycleOut)
def contribute(
    pool_id: int,
    payload: ContributeRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    pool, membership = _get_pool_and_membership(db, pool_id, user)
    cycle = _current_cycle(db, pool)
    if cycle.status != "collecting":
        raise HTTPException(status_code=400, detail="This cycle is not collecting contributions")
    if len(pool.memberships) < pool.member_cap:
        raise HTTPException(
            status_code=400,
            detail=f"Waiting for more members to join ({len(pool.memberships)}/{pool.member_cap}) before cycles can start",
        )

    already = (
        db.query(LedgerEntry)
        .filter(
            LedgerEntry.cycle_id == cycle.id,
            LedgerEntry.membership_id == membership.id,
            LedgerEntry.entry_type == "contribution",
        )
        .first()
    )
    if already is not None:
        raise HTTPException(status_code=400, detail="Already contributed this cycle")

    db.add(
        LedgerEntry(
            pool_id=pool.id,
            membership_id=membership.id,
            cycle_id=cycle.id,
            entry_type="contribution",
            amount=pool.contribution_amount,
            on_time=payload.on_time,
        )
    )
    membership.total_contributions_count += 1
    if payload.on_time:
        membership.on_time_count += 1

    contributed_count = (
        db.query(LedgerEntry)
        .filter(LedgerEntry.cycle_id == cycle.id, LedgerEntry.entry_type == "contribution")
        .count()
        + 1
    )
    if contributed_count >= len(pool.memberships):
        cycle.status = "bidding_open"

    db.commit()
    db.refresh(cycle)
    return _cycle_out(cycle, db)


@router.post("/bid", response_model=BidOut)
def submit_bid(
    pool_id: int,
    payload: BidCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    pool, membership = _get_pool_and_membership(db, pool_id, user)
    cycle = _current_cycle(db, pool)
    if cycle.status != "bidding_open":
        raise HTTPException(status_code=400, detail="Bidding is not open for this cycle")
    if membership.has_won:
        raise HTTPException(status_code=400, detail="You already won a payout in this pool")
    pool_total = pool.contribution_amount * len(pool.memberships)
    if payload.amount > pool_total:
        raise HTTPException(status_code=400, detail=f"Bid cannot exceed pool total of {pool_total}")

    existing = db.query(BidModel).filter(BidModel.cycle_id == cycle.id, BidModel.membership_id == membership.id).first()
    if existing is not None:
        existing.amount = payload.amount
        bid = existing
    else:
        bid = BidModel(cycle_id=cycle.id, membership_id=membership.id, amount=payload.amount)
        db.add(bid)

    db.commit()
    db.refresh(bid)
    return BidOut(id=bid.id, membership_id=bid.membership_id, member_name=user.name, amount=bid.amount)


@router.post("/cycles/current/resolve", response_model=CycleOut)
def resolve_cycle(pool_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    pool, _ = _get_pool_and_membership(db, pool_id, user)
    cycle = _current_cycle(db, pool)
    if cycle.status != "bidding_open":
        raise HTTPException(status_code=400, detail="Bidding is not open for this cycle")

    all_memberships = pool.memberships
    eligible_ids = [m.id for m in all_memberships if not m.has_won]
    all_ids = [m.id for m in all_memberships]
    pool_total = pool.contribution_amount * len(all_memberships)

    db_bids = db.query(BidModel).filter(BidModel.cycle_id == cycle.id).order_by(BidModel.created_at).all()
    engine_bids = [
        EngineBid(membership_id=b.membership_id, amount=b.amount, order=i) for i, b in enumerate(db_bids)
    ]

    result = resolve_cycle_bids(
        pool_total=pool_total,
        eligible_membership_ids=eligible_ids,
        all_membership_ids=all_ids,
        bids=engine_bids,
    )

    cycle.status = "resolved"
    cycle.winner_membership_id = result.winner_membership_id
    cycle.winning_bid_amount = result.winning_amount
    cycle.dividend_per_member = result.dividend_per_member

    winner_membership = db.get(Membership, result.winner_membership_id)
    winner_membership.has_won = True

    db.add(
        LedgerEntry(
            pool_id=pool.id,
            membership_id=result.winner_membership_id,
            cycle_id=cycle.id,
            entry_type="payout",
            amount=result.winning_amount,
        )
    )
    if result.dividend_per_member > 0:
        for recipient_id in result.dividend_recipient_ids:
            db.add(
                LedgerEntry(
                    pool_id=pool.id,
                    membership_id=recipient_id,
                    cycle_id=cycle.id,
                    entry_type="dividend",
                    amount=result.dividend_per_member,
                )
            )

    if pool.current_cycle_number >= pool.member_cap:
        pool.status = "completed"
    else:
        pool.current_cycle_number += 1
        db.add(Cycle(pool_id=pool.id, cycle_number=pool.current_cycle_number, status="collecting"))

    db.commit()
    db.refresh(cycle)
    return _cycle_out(cycle, db)


@router.get("/ledger", response_model=list[LedgerEntryOut])
def get_ledger(pool_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    pool, _ = _get_pool_and_membership(db, pool_id, user)
    entries = (
        db.query(LedgerEntry)
        .filter(LedgerEntry.pool_id == pool.id)
        .order_by(LedgerEntry.created_at.desc())
        .all()
    )
    out = []
    for e in entries:
        membership = db.get(Membership, e.membership_id)
        out.append(
            LedgerEntryOut(
                id=e.id,
                membership_id=e.membership_id,
                member_name=membership.user.name,
                cycle_id=e.cycle_id,
                entry_type=e.entry_type,
                amount=e.amount,
                on_time=e.on_time,
                created_at=e.created_at,
            )
        )
    return out
