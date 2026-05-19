import json, pathlib, time, argparse
from src.llm import DeepSeekClient
from src.pipeline import handle
from src.guardrail import check_no_overpromise
from eval.baseline import baseline_handle
from eval.metrics import score

DATA = pathlib.Path(__file__).parent.parent / "data"

def run(which, limit=0):
    rows = [json.loads(l) for l in (DATA/"testset.jsonl").read_text().splitlines() if l.strip()]
    if limit > 0:
        rows = rows[:limit]
    llm = DeepSeekClient()
    preds, ophits = [], []
    t0 = time.time()
    for r in rows:
        out = (handle(r["message"], llm) if which=="agent"
               else baseline_handle(r["message"], llm))
        preds.append({"category":out.get("category",""),
                      "decision":out.get("decision","auto"),
                      "citations":out.get("citations",[])})
        ophits.append(bool(check_no_overpromise(out.get("reply_zh","")+out.get("reply_en",""))))
    dt = time.time()-t0
    s = score(preds, rows, ophits); s["avg_sec"] = round(dt/len(rows),2)
    return s

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--which", default="agent")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    print(json.dumps(run(a.which, a.limit), ensure_ascii=False, indent=2))
