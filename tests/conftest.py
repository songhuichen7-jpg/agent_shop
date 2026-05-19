import json, pathlib, pytest

# 共享数据目录，供后续 test 模块 (test_data_integrity 等) 导入使用
DATA = pathlib.Path(__file__).parent.parent / "data"

class FakeLLM:
    """确定性 LLM 桩：按注册的 (tag -> dict) 返回 dict。"""
    def __init__(self, responses=None):
        self.responses = responses or {}
        self.calls = []
    def complete_json(self, prompt: str, tag: str) -> dict:
        self.calls.append((tag, prompt))
        if tag not in self.responses:
            raise AssertionError(f"FakeLLM 未注册 tag={tag}")
        return self.responses[tag]

@pytest.fixture
def fake_llm():
    return FakeLLM()

@pytest.fixture
def sample_orders(tmp_path):
    orders = [
        {"order_id": "BF1001", "merchant_id": "M01", "route": "CN-ZA",
         "status": "清关中", "events": [{"ts": "2026-05-10", "desc": "到达约堡海关"}],
         "exception": None, "ship_date": "2026-05-05"},
        {"order_id": "BF1002", "merchant_id": "M01", "route": "CN-ZA",
         "status": "丢件", "events": [{"ts": "2026-05-08", "desc": "末端派送异常"}],
         "exception": "lost", "ship_date": "2026-05-01"},
    ]
    p = tmp_path / "orders.json"
    p.write_text(json.dumps(orders, ensure_ascii=False))
    return p

@pytest.fixture
def sample_policy(tmp_path):
    kb = [
        {"clause_id": "P-TIME-01", "category": "物流时效",
         "zh": "CN-ZA 标准时效为发货后 7-12 个工作日，清关延误不计入。",
         "en": "Standard CN-ZA lead time is 7-12 business days after dispatch; customs delays excluded."},
        {"clause_id": "P-LOST-01", "category": "丢件破损",
         "zh": "确认丢件后按申报价值赔付，需 5 个工作日核实。",
         "en": "Confirmed lost parcels are compensated at declared value after a 5-business-day verification."},
    ]
    p = tmp_path / "policy_kb.json"
    p.write_text(json.dumps(kb, ensure_ascii=False))
    return p
