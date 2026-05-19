from src.order_lookup import lookup_order

def test_lookup_hit(sample_orders):
    o = lookup_order("BF1001", path=sample_orders)
    assert o["status"] == "清关中" and o["route"] == "CN-ZA"

def test_lookup_miss(sample_orders):
    assert lookup_order("NOPE", path=sample_orders) is None
