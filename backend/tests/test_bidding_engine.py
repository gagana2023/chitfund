import pytest

from app.services.bidding_engine import Bid, resolve_cycle_bids


def test_lowest_bid_wins_and_dividend_splits_to_others():
    result = resolve_cycle_bids(
        pool_total=300.0,
        eligible_membership_ids=[1, 2, 3],
        all_membership_ids=[1, 2, 3],
        bids=[
            Bid(membership_id=1, amount=280.0, order=0),
            Bid(membership_id=2, amount=250.0, order=1),
            Bid(membership_id=3, amount=290.0, order=2),
        ],
    )
    assert result.winner_membership_id == 2
    assert result.winning_amount == 250.0
    assert result.discount == 50.0
    assert result.dividend_per_member == 25.0
    assert set(result.dividend_recipient_ids) == {1, 3}


def test_tied_bids_break_by_earliest_submission():
    result = resolve_cycle_bids(
        pool_total=300.0,
        eligible_membership_ids=[1, 2],
        all_membership_ids=[1, 2],
        bids=[
            Bid(membership_id=1, amount=250.0, order=1),
            Bid(membership_id=2, amount=250.0, order=0),
        ],
    )
    assert result.winner_membership_id == 2


def test_no_bids_falls_back_to_full_pool_no_discount():
    result = resolve_cycle_bids(
        pool_total=300.0,
        eligible_membership_ids=[5, 6],
        all_membership_ids=[1, 5, 6],
        bids=[],
    )
    assert result.winner_membership_id == 5
    assert result.winning_amount == 300.0
    assert result.discount == 0.0
    assert result.dividend_per_member == 0.0


def test_bid_above_pool_total_is_rejected():
    with pytest.raises(ValueError):
        resolve_cycle_bids(
            pool_total=300.0,
            eligible_membership_ids=[1],
            all_membership_ids=[1],
            bids=[Bid(membership_id=1, amount=400.0, order=0)],
        )


def test_ineligible_members_bids_are_ignored():
    result = resolve_cycle_bids(
        pool_total=300.0,
        eligible_membership_ids=[2],
        all_membership_ids=[1, 2],
        bids=[
            Bid(membership_id=1, amount=100.0, order=0),  # already won, ignored
            Bid(membership_id=2, amount=280.0, order=1),
        ],
    )
    assert result.winner_membership_id == 2
    assert result.winning_amount == 280.0
