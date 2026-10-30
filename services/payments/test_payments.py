import pytest

from payments import apply_fee


def test_fee():
    assert apply_fee(100) == 102.5


def test_negative_amount():
    with pytest.raises(ValueError):
        apply_fee(-1)
