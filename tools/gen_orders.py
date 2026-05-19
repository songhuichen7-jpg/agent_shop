import json, random, pathlib
random.seed(42)
STATUSES = ["在途","清关中","已签收","异常","退件","丢件"]
rows=[]
for i in range(300):
    st = STATUSES[i % len(STATUSES)] if i < 60 else random.choice(STATUSES)
    rows.append({
      "order_id": f"BF{1000+i}",
      "merchant_id": f"M{random.randint(1,20):02d}",
      "route": "CN-ZA",
      "status": st,
      "events": [{"ts": "2026-05-%02d" % random.randint(1,18),
                  "desc": {"在途":"干线运输中","清关中":"约堡海关查验",
                           "已签收":"已签收","异常":"末端派送异常",
                           "退件":"退回发件仓","丢件":"轨迹中断超时"}[st]}],
      "exception": {"异常":"delivery_fail","丢件":"lost","退件":"returned"}.get(st),
      "ship_date": "2026-05-%02d" % random.randint(1,10),
    })
pathlib.Path("data/orders.json").write_text(json.dumps(rows, ensure_ascii=False, indent=0))
