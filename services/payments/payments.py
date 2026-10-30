def apply_fee(amount: float, fee_pct: float = 2.5) -> float:
    """Return the amount plus a percentage processing fee."""
    if amount < 0:
        raise ValueError("amount must be positive")
    return round(amount * (1 + fee_pct / 100), 2)
