import pathlib
REF = pathlib.Path(__file__).parent.parent / "skill" / "references"

def load_reference(name: str) -> str:
    return (REF / name).read_text(encoding="utf-8")
