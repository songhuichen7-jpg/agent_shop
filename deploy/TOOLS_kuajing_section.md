
<!-- AGENT_SHOP_KUAJING:BEGIN (managed by deploy/wire_agents_md.sh — 勿手改) -->
---

## agent_shop pipeline — 环境与命令（本机特定）

- 仓库（容器只读挂载）：`/home/node/agent_shop`（宿主 `~/openclaw-agent-shop/agent_shop`）。
- 环境变量：`/home/node/agent_shop/.env`（线上回复默认 `ONLINE_LLM_PROVIDER=deepseek`、`ONLINE_LLM_MODEL=deepseek-v4-flash`、`DEEPSEEK_API_KEY`/`ONLINE_LLM_KEY`、`FEISHU_BITABLE_APP_TOKEN`、`FEISHU_BITABLE_TABLE_ID`、`FEISHU_HUMAN_CHAT_ID`，可选 `FEISHU_TASK_ASSIGNEE_ID`）。用前 `set -a; . /home/node/agent_shop/.env; set +a`。
- 大脑：`python3 /home/node/agent_shop/skill/scripts/run_pipeline.py "<商户消息原文>"` → 输出契约 JSON。容器 python 无 pip，LLM 客户端内置 stdlib urllib 回退，零依赖。
- 飞书动作：`bash /home/node/agent_shop/skill/scripts/feishu_actions.sh {log|escalate|reply} ...`。它经 `skill/scripts/lark.sh` 调 lark-cli；服务器优先使用**持久化已授权配置** `HOME=/home/node/runtime/larkhome`，本地开发可用 `LARK_CLI_BIN` / PATH 回退。
- lark-cli 1.0.34：多维表格命令 `base`（非 `bitable`）；`im +messages-send` 与 `base +record-batch-create` 不支持 `--format json`，`task +create` 支持。看板列：`原始消息 / 类目 / 决策 / 中文回复 / 英文回复 / 引用条款 / 订单号 / 消息ID / 创建时间 / 紧急度 / 处理状态 / 升级原因`。
- 数据全合成，订单库仅 `BF1000–BF1299`；查不到订单即按 escalate（脚本已处理）。
- 回滚：工作区是 git 仓，`git -C /home/node/.openclaw/workspace log` 见还原点。
<!-- AGENT_SHOP_KUAJING:END -->
