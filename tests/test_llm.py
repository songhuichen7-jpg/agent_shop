from src.llm import parse_json_text


def test_parse_json_text_plain():
    assert parse_json_text('{"ok": true}') == {"ok": True}


def test_parse_json_text_fenced_json():
    assert parse_json_text('```json\n{"ok": true}\n```') == {"ok": True}
