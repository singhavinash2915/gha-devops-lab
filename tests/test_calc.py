import pytest

from app.calc import add, divide, percent


def test_add():
    assert add(2, 3) == 5


def test_divide():
    assert divide(10, 4) == 2.5


def test_divide_by_zero():
    with pytest.raises(ValueError):
        divide(1, 0)


@pytest.mark.parametrize("part,whole,expected", [(1, 4, 25.0), (2, 3, 66.7), (5, 5, 100.0)])
def test_percent(part, whole, expected):
    assert percent(part, whole) == expected
