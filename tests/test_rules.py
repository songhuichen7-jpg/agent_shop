from src.rules import load_reference

def test_load_reference_reads_skill_references():
    txt = load_reference("classify_prompt.md")
    assert "类目" in txt and len(txt) > 50
