import json
import os
import subprocess


def _fake_lark(tmp_path):
    calls = tmp_path / "calls.jsonl"
    fake = tmp_path / "lark-cli"
    fake.write_text(
        "#!/usr/bin/env bash\n"
        "python3 - \"$@\" <<'PY'\n"
        "import json, os, sys\n"
        "with open(os.environ['FAKE_LARK_CALLS'], 'a', encoding='utf-8') as f:\n"
        "    f.write(json.dumps({'args': sys.argv[1:]}, ensure_ascii=False) + '\\n')\n"
        "print('{\"ok\":true}')\n"
        "PY\n"
    )
    fake.chmod(0o755)
    return fake, calls


def test_log_writes_full_bitable_payload(tmp_path):
    fake, calls = _fake_lark(tmp_path)
    env = {
        **os.environ,
        "LARK_CLI_BIN": str(fake),
        "FAKE_LARK_CALLS": str(calls),
        "FEISHU_BITABLE_APP_TOKEN": "app_xxx",
        "FEISHU_BITABLE_TABLE_ID": "tbl_xxx",
    }
    contract = {
        "message": "请查 BF1002",
        "order_id": "BF1002",
        "category": "物流时效",
        "urgency": "normal",
        "decision": "auto",
        "reply_zh": "中文",
        "reply_en": "English",
        "citations": ["P-TIME-01"],
        "escalate_reason": "",
        "message_id": "msg_abc",
        "created_at": "2026-05-20 10:11:12",
    }

    subprocess.run(
        ["bash", "skill/scripts/feishu_actions.sh", "log", json.dumps(contract, ensure_ascii=False)],
        check=True,
        env=env,
    )

    call = json.loads(calls.read_text().splitlines()[0])
    payload = json.loads(call["args"][call["args"].index("--json") + 1])
    assert payload["fields"] == [
        "原始消息",
        "类目",
        "决策",
        "中文回复",
        "英文回复",
        "引用条款",
        "订单号",
        "消息ID",
        "创建时间",
        "紧急度",
        "处理状态",
        "升级原因",
    ]
    assert payload["rows"][0] == [
        "请查 BF1002",
        "物流时效",
        "auto",
        "中文",
        "English",
        "P-TIME-01",
        "BF1002",
        "msg_abc",
        "2026-05-20 10:11:12",
        "medium",
        "已自动回复",
        None,
    ]


def test_escalate_uses_idempotency_key_when_message_id_present(tmp_path):
    fake, calls = _fake_lark(tmp_path)
    env = {
        **os.environ,
        "LARK_CLI_BIN": str(fake),
        "FAKE_LARK_CALLS": str(calls),
        "FEISHU_MESSAGE_ID": "msg_123",
    }

    subprocess.run(
        ["bash", "skill/scripts/feishu_actions.sh", "escalate", "客诉升级: 丢件破损", "body"],
        check=True,
        env=env,
    )

    call = json.loads(calls.read_text().splitlines()[0])
    assert "--idempotency-key" in call["args"]
    assert call["args"][call["args"].index("--idempotency-key") + 1] == "msg_123"
