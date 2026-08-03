from datetime import datetime

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    pin: str = Field(min_length=3, max_length=32)


class UserOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class PoolCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    contribution_amount: float = Field(gt=0)
    member_cap: int = Field(ge=2, le=50)


class PoolJoin(BaseModel):
    invite_code: str


class MemberOut(BaseModel):
    membership_id: int
    user_id: int
    name: str
    is_head: bool
    has_won: bool
    trust_score: float

    class Config:
        from_attributes = True


class PoolOut(BaseModel):
    id: int
    name: str
    contribution_amount: float
    member_cap: int
    invite_code: str
    current_cycle_number: int
    status: str
    member_count: int

    class Config:
        from_attributes = True


class PoolDetailOut(PoolOut):
    members: list[MemberOut]


class PoolPublicOut(BaseModel):
    id: int
    name: str
    contribution_amount: float
    member_cap: int
    current_cycle_number: int
    status: str
    member_count: int
    head_name: str
    is_member: bool
    has_pending_request: bool

    class Config:
        from_attributes = True


class JoinRequestOut(BaseModel):
    id: int
    pool_id: int
    user_id: int
    requester_name: str
    status: str

    class Config:
        from_attributes = True


class ContributeRequest(BaseModel):
    on_time: bool = True


class LedgerEntryOut(BaseModel):
    id: int
    membership_id: int
    member_name: str
    cycle_id: int | None
    entry_type: str
    amount: float
    on_time: bool | None
    created_at: datetime

    class Config:
        from_attributes = True


class CycleOut(BaseModel):
    id: int
    cycle_number: int
    status: str
    winner_membership_id: int | None
    winner_name: str | None
    winning_bid_amount: float | None
    dividend_per_member: float | None

    class Config:
        from_attributes = True


class BidCreate(BaseModel):
    amount: float = Field(ge=0)


class BidOut(BaseModel):
    id: int
    membership_id: int
    member_name: str
    amount: float

    class Config:
        from_attributes = True
