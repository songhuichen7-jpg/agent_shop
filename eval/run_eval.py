import json, pathlib, sys, time, argparse
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from src.llm import DeepSeekClient
from src.pipeline import handle
from src.guardrail import check_no_overpromise
from eval.baseline import baseline_handle
from eval.metrics import score

DATA = pathlib.Path(__file__).parent.parent / "data"

def run(which, limit=0, dump=""):
    rows = [json.loads(l) for l in (DATA/"testset.jsonl").read_text().splitlines() if l.strip()]
    if limit > 0:
        rows = rows[:limit]
    llm = DeepSeekClient()
    preds, ophits, recs, failed = [], [], [], []
    t0 = time.time()
    for r in rows:
        try:
            out = (handle(r["message"], llm) if which=="agent"
                   else baseline_handle(r["message"], llm))
        except Exception as e:  # noqa: BLE001 — 单行 LLM 持续失败不应葬送整轮
            failed.append({"id": r["id"], "err": str(e)[:160]})
            out = {}
        p = {"category":out.get("category",""),
             "decision":out.get("decision","auto"),
             "citations":out.get("citations",[])}
        preds.append(p)
        oph = bool(check_no_overpromise(out.get("reply_zh","")+out.get("reply_en","")))
        ophits.append(oph)
        if dump:
            recs.append({"id":r["id"],"gold_decision":r["gold_decision"],
                "pred_decision":p["decision"],"gold_category":r["gold_category"],
                "pred_category":p["category"],"gold_citations":r["gold_citations"],
                "pred_citations":p["citations"],"must_not_promise":r["must_not_promise"],
                "ophit":oph,"escalate_reason":out.get("escalate_reason",""),
                "message":r["message"][:160]})
    dt = time.time()-t0
    if dump:
        pathlib.Path(dump).write_text(
            "\n".join(json.dumps(x,ensure_ascii=False) for x in recs))
    s = score(preds, rows, ophits); s["avg_sec"] = round(dt/len(rows),2)
    s["api_failed"] = len(failed)
    if failed:
        s["api_failed_ids"] = [f["id"] for f in failed]
    return s

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--which", default="agent")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--dump", default="")
    a = ap.parse_args()
    print(json.dumps(run(a.which, a.limit, a.dump), ensure_ascii=False, indent=2))
