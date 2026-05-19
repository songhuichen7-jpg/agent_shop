
---

## 跨境客诉助手 (agent_shop) — 飞书客诉自动处理 [硬性流程]

当飞书收到的消息是**跨境 B2C 物流的商户咨询/客诉**（中文/英文/中英混；常见：物流时效、丢件破损、费用对账、清关、退件、一般咨询；可能带订单号形如 `BF1234`），你**必须**走下面流程，不要凭自己知识直接闲聊作答：

1. 运行（用 exec，`MSG` 替换为商户原始消息原文，不要改写）：

   ```
   set -a; . /home/node/agent_shop/.env; set +a; \
   python3 /home/node/agent_shop/skill/scripts/run_pipeline.py "MSG"
   ```

   它会输出一行 JSON，含 `category/decision/citations/order_facts/reply_zh/reply_en/escalate_reason`。

2. 严格按 JSON 的 `decision` 行动：
   - `decision == "auto"`：用**飞书原生回复**把 `reply_zh` 和 `reply_en` 回给商户（两段都发，保持双语）。然后调一次看板记录：
     ```
     /home/node/runtime/npm/node_modules/.bin/lark-cli base +record-batch-create --as user \
       --base-token "$FEISHU_BITABLE_APP_TOKEN" --table-id "$FEISHU_BITABLE_TABLE_ID" \
       --json '{"fields":["类目","决策","升级原因"],"rows":[["<category>","auto","<citations 逗号拼接 或 - >"]]}'
     ```
     （`$FEISHU_BITABLE_*` 来自 `/home/node/agent_shop/.env`，先 source 它。）
   - `decision == "escalate"`：**不要**把敏感结论（赔付金额、时效承诺、清关结果）直接答复商户。只回一句中性话术（如「您的问题已转人工跟进，稍后联系您 / Your case has been escalated to a human agent」），并建飞书任务：
     ```
     /home/node/runtime/npm/node_modules/.bin/lark-cli task +create --as user \
       --summary "客诉升级: <category>" \
       --description "原因:<escalate_reason> 引用:<citations> 商户消息:<MSG 摘要>" --format json
     ```

3. 红线：不得自行编造政策、不得承诺具体到货天数/赔付金额/保证清关；`run_pipeline.py` 没给依据就按 escalate 处理；脚本报错时，回中性话术并按 escalate 建任务，不要硬答。

4. 非跨境物流客诉的普通消息，照常正常对话，不走本流程。

环境与命令细节见 `TOOLS.md` 的「agent_shop pipeline」节。
