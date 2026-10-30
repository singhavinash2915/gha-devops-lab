from orders import order_total


def test_order_total():
    assert order_total([{"qty": 2, "price": 10.0}, {"qty": 1, "price": 5.5}]) == 25.5


def test_empty_order():
    assert order_total([]) == 0
