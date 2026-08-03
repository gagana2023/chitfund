from dataclasses import dataclass


@dataclass(frozen=True)
class Bid:
    membership_id: int
    amount: float
    order: int  # submission order, lower = earlier


@dataclass(frozen=True)
class ResolvedCycle:
    winner_membership_id: int
    winning_amount: float
    discount: float
    dividend_per_member: float
    dividend_recipient_ids: list[int]


def resolve_cycle_bids(
    pool_total: float,
    eligible_membership_ids: list[int],
    all_membership_ids: list[int],
    bids: list[Bid],
) -> ResolvedCycle:
    """Resolve one bidding round.

    Lowest bid wins the payout (at their bid amount, not the full pool).
    Ties break by earliest submission. The gap between the pool total and
    the winning bid (the "discount") is split evenly as a dividend across
    every other member of the pool - including members who already won,
    since real chit-fund subscribers keep contributing every cycle.
    No bids -> the first eligible member takes the full pool, no discount.
    """
    if not eligible_membership_ids:
        raise ValueError("No eligible members to win this cycle")

    eligible_bids = [b for b in bids if b.membership_id in eligible_membership_ids]
    for b in eligible_bids:
        if b.amount < 0 or b.amount > pool_total:
            raise ValueError(f"Bid {b.amount} out of range [0, {pool_total}]")

    if eligible_bids:
        winning_bid = min(eligible_bids, key=lambda b: (b.amount, b.order))
        winner_id = winning_bid.membership_id
        winning_amount = winning_bid.amount
    else:
        winner_id = eligible_membership_ids[0]
        winning_amount = pool_total

    discount = pool_total - winning_amount
    recipients = [m for m in all_membership_ids if m != winner_id]
    dividend_per_member = discount / len(recipients) if recipients else 0.0

    return ResolvedCycle(
        winner_membership_id=winner_id,
        winning_amount=winning_amount,
        discount=discount,
        dividend_per_member=dividend_per_member,
        dividend_recipient_ids=recipients,
    )
