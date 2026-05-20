import importlib.util
import json
import subprocess


def _load_run_pipeline():
    spec = importlib.util.spec_from_file_location("run_pipeline_script", "skill/scripts/run_pipeline.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_side_effect_adds_message_to_log_payload(monkeypatch):
    module = _load_run_pipeline()
    calls = []

    def fake_run(args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, stdout='{"ok":true}', stderr="")

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    module._side_effect({"decision": "auto", "order_id": "BF1002"}, "请查 BF1002")

    payload = json.loads(calls[0][3])
    assert payload["message"] == "请查 BF1002"
    assert payload["order_id"] == "BF1002"


def test_side_effect_reports_lark_failures(monkeypatch, capsys):
    module = _load_run_pipeline()

    def fake_run(args, **kwargs):
        return subprocess.CompletedProcess(args, 1, stdout="", stderr="permission denied")

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    module._side_effect(
        {"decision": "escalate", "category": "丢件破损", "escalate_reason": "需人工", "citations": []},
        "商户消息",
    )

    err = capsys.readouterr().err
    assert "feishu log failed" in err
    assert "feishu escalate failed" in err
