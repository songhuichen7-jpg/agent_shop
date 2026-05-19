
---

## agent_shop pipeline — 环境与命令（本机特定）

- 仓库（容器内只读挂载）：`/home/node/agent_shop`（宿主 `~/openclaw-agent-shop/agent_shop`）。
- 环境变量：`/home/node/agent_shop/.env`（含 `DEEPSEEK_API_KEY`、`DEEPSEEK_BASE_URL`、`DEEPSEEK_EVAL_MODEL`、`FEISHU_BITABLE_APP_TOKEN`、`FEISHU_BITABLE_TABLE_ID`、`FEISHU_HUMAN_CHAT_ID`）。用前 `set -a; . /home/node/agent_shop/.env; set +a`。
- 大脑入口：`python3 /home/node/agent_shop/skill/scripts/run_pipeline.py "<商户消息原文>"` → 打印输出契约 JSON。容器 python 无 pip，`DeepSeekClient` 已内置 stdlib urllib 回退，零依赖可跑。
- lark-cli：`/home/node/runtime/npm/node_modules/.bin/lark-cli`（1.0.34，装在持久卷）。多维表格命令是 `base`（非 `bitable`）；`im +messages-send` 与 `base +record-batch-create` **不支持** `--format json`，`task +create` 支持。看板文本列名是「升级原因」（非「备注」）。
- 多维表格「客诉看板」列：`类目 / 决策 / 升级原因`。人工群：`$FEISHU_HUMAN_CHAT_ID`。
- 数据全合成，订单库仅 `BF1000–BF1299`；查不到订单即按 escalate（脚本已处理）。
- 回滚：本工作区是 git 仓，`git -C /home/node/.openclaw/workspace log` 可见还原点；误改用 `git reset --hard <sha>`。
