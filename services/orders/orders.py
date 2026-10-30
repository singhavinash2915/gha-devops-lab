def order_total(items: list[dict]) -> float:
    """Sum quantity * price for each line item."""
    return round(sum(i["qty"] * i["price"] for i in items), 2)
