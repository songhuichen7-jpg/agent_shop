import json, pathlib
_DEFAULT = pathlib.Path(__file__).parent.parent / "data" / "orders.json"

def lookup_order(order_id: str, path=None):
    data = json.loads(pathlib.Path(path or _DEFAULT).read_text())
    for o in data:
        if o["order_id"] == order_id:
            return o
    return None
