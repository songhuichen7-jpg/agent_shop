
<!-- AGENT_SHOP_KUAJING:BEGIN (managed by deploy/wire_agents_md.sh — 勿手改) -->
---

## 跨境客诉助手 (agent_shop) — 飞书客诉自动处理 [硬性流程]

飞书消息若是**跨境 B2C 物流的商户咨询/客诉**（中/英/混；物流时效、丢件破损、费用对账、清关、退件、一般咨询；常带订单号 `BF1234`），**必须**走下面流程，不要凭自己知识闲聊作答：

1. 用 exec 跑大脑（`MSG` 替换为商户原始消息原文，勿改写）：

   ```
   set -a; . /home/node/agent_shop/.env; set +a; \
   python3 /home/node/agent_shop/skill/scripts/run_pipeline.py "MSG"
   ```

   输出一行 JSON：`category/order_id/decision/citations/order_facts/reply_zh/reply_en/escalate_reason`。**该脚本会自动把本次案例写入飞书多维表格看板；若 decision=escalate 还会自动建飞书任务**——你无需另外调任何 shell。飞书动作失败时会写入 stderr，主 JSON 仍会正常输出。

2. 按 JSON 的 `decision` 用**飞书原生回复**作答：
   - `auto`：把 `reply_zh` 和 `reply_en` 两段都回给商户（保持双语）。
   - `escalate`：**不要**把敏感结论（赔付金额/时效承诺/清关结果）答给商户，只回中性话术：`您的问题已转人工跟进，稍后联系您 / Your case has been escalated to a human agent.`

3. 红线：不编造政策、不承诺具体到货天数/赔付金额/保证清关；`run_pipeline.py` 无依据即按 escalate；脚本报错则回中性话术，不要硬答（任务即便没建出来，agent 也不可代赔代承诺）。

4. 非跨境物流客诉的普通消息照常正常对话，不走本流程。

环境与命令细节见 `TOOLS.md`「agent_shop pipeline」节。
<!-- AGENT_SHOP_KUAJING:END -->
