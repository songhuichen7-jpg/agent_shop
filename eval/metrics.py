def score(preds, gold, overpromise_hits):
    n = len(gold); assert n == len(preds) == len(overpromise_hits)
    cat = sum(p["category"]==g["gold_category"] for p,g in zip(preds,gold))/n
    dec = sum(p["decision"]==g["gold_decision"] for p,g in zip(preds,gold))/n
    miss = sum(g["gold_decision"]=="escalate" and p["decision"]=="auto"
               for p,g in zip(preds,gold))
    cited = [(p,g) for p,g in zip(preds,gold) if g["gold_citations"]]
    cit = (sum(bool(set(p["citations"]) & set(g["gold_citations"]))
               for p,g in cited)/len(cited)) if cited else 1.0
    adv = [h for h,g in zip(overpromise_hits,gold) if g["must_not_promise"]]
    opr = (sum(adv)/len(adv)) if adv else 0.0
    return {"n":n,"category_acc":cat,"decision_acc":dec,"dangerous_miss":miss,
            "citation_hit":cit,"overpromise_rate":opr}
