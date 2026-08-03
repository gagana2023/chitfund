import secrets
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def gen_invite_code() -> str:
    return secrets.token_hex(4)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Not unique: different people can share a display name. Identity is the
    # (name, pin_hash) pair - see app.security for the login matching logic.
    name: Mapped[str] = mapped_column(String(64), index=True)
    pin_hash: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)


class Pool(Base):
    __tablename__ = "pools"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    contribution_amount: Mapped[float] = mapped_column(Float)
    member_cap: Mapped[int] = mapped_column(Integer)
    invite_code: Mapped[str] = mapped_column(String(16), unique=True, index=True, default=gen_invite_code)
    current_cycle_number: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(16), default="active")  # active | completed
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)

    memberships: Mapped[list["Membership"]] = relationship(back_populates="pool")
    cycles: Mapped[list["Cycle"]] = relationship(back_populates="pool")


class Membership(Base):
    __tablename__ = "memberships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pool_id: Mapped[int] = mapped_column(ForeignKey("pools.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    is_head: Mapped[bool] = mapped_column(Boolean, default=False)
    has_won: Mapped[bool] = mapped_column(Boolean, default=False)
    on_time_count: Mapped[int] = mapped_column(Integer, default=0)
    total_contributions_count: Mapped[int] = mapped_column(Integer, default=0)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)

    pool: Mapped["Pool"] = relationship(back_populates="memberships")
    user: Mapped["User"] = relationship()


class Cycle(Base):
    __tablename__ = "cycles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pool_id: Mapped[int] = mapped_column(ForeignKey("pools.id"))
    cycle_number: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(24), default="collecting")  # collecting | bidding_open | resolved
    winner_membership_id: Mapped[int | None] = mapped_column(ForeignKey("memberships.id"), nullable=True)
    winning_bid_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    dividend_per_member: Mapped[float | None] = mapped_column(Float, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)

    pool: Mapped["Pool"] = relationship(back_populates="cycles")
    bids: Mapped[list["Bid"]] = relationship(back_populates="cycle")


class Bid(Base):
    __tablename__ = "bids"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cycle_id: Mapped[int] = mapped_column(ForeignKey("cycles.id"))
    membership_id: Mapped[int] = mapped_column(ForeignKey("memberships.id"))
    amount: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)

    cycle: Mapped["Cycle"] = relationship(back_populates="bids")


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pool_id: Mapped[int] = mapped_column(ForeignKey("pools.id"))
    membership_id: Mapped[int] = mapped_column(ForeignKey("memberships.id"))
    cycle_id: Mapped[int | None] = mapped_column(ForeignKey("cycles.id"), nullable=True)
    entry_type: Mapped[str] = mapped_column(String(16))  # contribution | payout | dividend
    amount: Mapped[float] = mapped_column(Float)
    on_time: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)


class JoinRequest(Base):
    __tablename__ = "join_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pool_id: Mapped[int] = mapped_column(ForeignKey("pools.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending | approved | rejected
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)

    user: Mapped["User"] = relationship()
