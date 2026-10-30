"""Small functions so the CI has something real to test."""


def add(a: float, b: float) -> float:
    return a + b


def divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("cannot divide by zero")
    return a / b


def percent(part: float, whole: float) -> float:
    """Return part/whole as a percentage rounded to one decimal place."""
    return round(divide(part, whole) * 100, 1)
