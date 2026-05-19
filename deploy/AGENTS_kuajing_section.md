
<!-- AGENT_SHOP_KUAJING:BEGIN (managed by deploy/wire_agents_md.sh — 勿手改) -->
---

## 跨境客诉助手 (agent_shop) — 飞书客诉自动处理 [硬性流程]

飞书消息若是**跨境 B2C 物流的商户咨询/客诉**（中/英/混；物流时效、丢件破损、费用对账、清关、退件、一般咨询；常带订单号 `BF1234`），**必须**走下面流程，不要凭自己知识闲聊作答：

1. 用 exec 跑大脑（`MSG` 替换为商户原始消息原文，勿改写）：

   ```
   set -a; . /home/node/agent_shop/.env; set +a; \
   python3 /home/node/agent_shop/skill/scripts/run_pipeline.py "MSG"
   ```

   输出一行 JSON：`category/decision/citations/order_facts/reply_zh/reply_en/escalate_reason`。把这行 JSON 原样记为 `J`。

2. 先 source 环境（飞书动作脚本需要）：`set -a; . /home/node/agent_shop/.env; set +a`

3. 按 `decision`：
   - `auto`：用**飞书原生回复**把 `reply_zh` 和 `reply_en` 两段都回给商户；然后记看板：
     ```
     bash /home/node/agent_shop/skill/scripts/feishu_actions.sh log 'J'
     ```
   - `escalate`：**不要**把敏感结论（赔付金额/时效承诺/清关结果）答复商户，只回中性话术（如「您的问题已转人工跟进，稍后联系您 / Your case has been escalated to a human agent」）；然后建飞书任务：
     ```
     bash /home/node/agent_shop/skill/scripts/feishu_actions.sh escalate "客诉升级: <category>" "原因:<escalate_reason> 引用:<citations> 商户消息:<MSG 摘要>"
     ```

4. 红线：不编造政策、不承诺具体到货天数/赔付金额/保证清关；`run_pipeline.py` 无依据即按 escalate；脚本报错则回中性话术并按 escalate 处理，不要硬答。

5. 非跨境物流客诉的普通消息照常正常对话，不走本流程。

命令/环境细节见 `TOOLS.md`「agent_shop pipeline」节。`feishu_actions.sh` 已内置 lark-cli 鉴权（经 `lark.sh` 指向持久化已授权配置），无需你再绑定。
<!-- AGENT_SHOP_KUAJING:END -->
