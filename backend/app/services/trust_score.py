def compute_trust_score(on_time_count: int, total_contributions_count: int) -> float:
    """Laplace-smoothed on-time ratio, scaled to 0-100.

    Smoothing (+1/+2) prevents a member with 1-2 contributions from reading
    as a perfect 100 - trust should build with history, not spike on it.
    """
    ratio = (on_time_count + 1) / (total_contributions_count + 2)
    return round(ratio * 100, 1)
