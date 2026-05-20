# 跨境物流客诉自动处理 Agent

> 一个建在 **OpenClaw(小龙虾) + 飞书 CLI + DeepSeek** 上的跨境 B2C 物流客诉自动处理 Agent。商户在飞书发来中英客诉 → 自动分类 → 查订单 → 引政策条款 → 起草双语回复 → 护栏拦乱承诺 → 决策（可答/升级）→ 飞书原生回复 + 多维表格看板自动落库 + 升级则建飞书任务派人工。**零过度承诺、零危险漏报、规则可解释**。

## 头条指标 (n=70 标注集，详见 [eval/SCORECARD.md](eval/SCORECARD.md))

| | **Agent** | Baseline（裸单 prompt LLM） |
|---|---:|---:|
| 升级判定准确率 | **84.3%** | 81.4% |
| 危险漏报（该升级却自动答） | **0** / 21 | 6 / 21 |
| 过度承诺率（对抗集触发） | **0.0%** | 8.3% |
| 引用命中率（回复必引政策条款） | **81.2%** | 0.0% |
| 分类准确率 | 91.4% | 94.3% |

差异化卖点：**零过度承诺 + 零危险漏报 + 81% 引用命中**（baseline 全 0）。决策准确反超 baseline。

## 演示

![demo](assets/demo-preview.gif)

> 上图为**前 18 秒预览**(自动循环)。**完整 48 秒 1080p 录屏**(60fps、含飞书原生回复 + 多维表格看板自动写入 + 对抗路径升级建任务全闭环):[`assets/demo.mp4`](assets/demo.mp4)(48 MB,点击下载播放)

## 架构

```
跨境商户在【飞书】发消息（中/英/混）
   ▼
OpenClaw（腾讯云，小龙虾） ── 飞书 Channel ── 「跨境客服」Agent
   ▼  agent 读 AGENTS.md → exec 调 run_pipeline.py
   ┌─────────────────────────────────────────────┐
   │ ① 分类 (LLM)           ② 查单 (mock 数据)     │
   │ ③ 取据 (政策 KB)        ④ 起草双语 (LLM)      │
   │ ⑤ 护栏 (有据+不乱承诺)   ⑥ 决策 (规则)         │
   │ ⑦ 副作用：飞书 CLI                          │
   │     auto    → 写多维表格看板                │
   │     escalate→ 建飞书任务 @人工              │
   └─────────────────────────────────────────────┘
   ▼ 返回契约 JSON
agent 用 reply_zh/reply_en 飞书原生回复商户
（escalate 时 agent 只回中性话术，不直接答敏感结论）
```

## 技术栈

- **OpenClaw 2026.5** ("小龙虾") — MIT 开源 AI Agent 执行网关，腾讯云 Lighthouse 一键部署
- **飞书 CLI 1.0.34** (`@larksuite/cli`) — 命令行调飞书开放平台 2500+ API
- **DeepSeek** — 在线 `deepseek-v4-flash`（OpenClaw 绑定），离线评测 `deepseek-v4-pro`（OpenAI 兼容接口）
- **Python 3.11** — `src/pipeline.py` 编排、`DeepSeekClient` 内置 stdlib urllib 回退（容器无 pip 也能跑）
- **腾讯云 Lighthouse** — 共 youshi 生产服务器（部署期间零影响 youshi 容器，全程 uptime 不变）
- **测试 / 评测** — pytest 47 单测全绿；离线评测 harness 含重试 + 逐行容错

## 仓库结构

```
agent_shop/
├── src/                       # 核心 Python：可导入库（TDD 覆盖）
│   ├── pipeline.py            #   主编排：classify→lookup→retrieve→draft→guardrail→decide
│   ├── classify.py            #   类目/紧急度/语言/情绪
│   ├── order_lookup.py        #   订单/物流状态查（mock JSON）
│   ├── policy_lookup.py       #   政策 grounded 检索（ascii 词 + 单汉字混合）
│   ├── draft.py               #   双语回复起草（强约束提示词）
│   ├── guardrail.py           #   两道护栏：有据校验 + 不乱承诺（带引用句豁免）
│   ├── decision.py            #   决策规则：威胁/硬承诺/赔款/海关查扣/签收报失/对账申诉
│   ├── llm.py                 #   DeepSeekClient（OpenAI SDK 优先，stdlib urllib 回退）
│   └── rules.py               #   规则/提示词单一事实源（从 skill/references 加载）
├── skill/                     # OpenClaw Skill 包（在线编排）
│   ├── SKILL.md               #   agent 行为说明（在线 OpenClaw 模型读取）
│   ├── references/            #   policy_kb / 提示词 / 升级规则 / lark cheatsheet
│   └── scripts/
│       ├── run_pipeline.py    #   在线入口：跑 pipeline + 自动写看板 / 建任务
│       ├── feishu_actions.sh  #   飞书动作封装：reply / log / escalate
│       └── lark.sh            #   lark-cli 包装（持久化已授权配置）
├── data/                      # 合成数据（不涉真实商户）
│   ├── policy_kb.json         #   26 条双语政策条款（中国→南非 B2C 跨境）
│   ├── orders.json            #   300 条 mock 订单（6 种状态全覆盖）
│   └── testset.jsonl          #   70 条标注客诉（21 升级 / 12 对抗）
├── eval/                      # 离线评测
│   ├── run_eval.py            #   harness（含 --dump 逐行诊断 + 容错）
│   ├── baseline.py            #   裸单 prompt baseline
│   ├── metrics.py             #   指标计算（纯函数 TDD）
│   ├── SCORECARD.md           #   评测记分卡（r0/r1/r2 全表 + Mimo 对照）
│   └── score_*.json / dump_*.jsonl  # 评测数据
├── tests/                     # pytest 47 测试（含数据完整性 + 规则 + 接线 + 评测指标）
├── deploy/                    # 服务器部署脚本
│   ├── openclaw_server_deploy.sh   # 幂等分阶段：prep/recreate/deps/discover/rollback
│   ├── wire_agents_md.sh           # AGENTS.md/TOOLS.md sentinel 注入（workspace git 备份）
│   ├── AGENTS_kuajing_section.md   # 注入到 OpenClaw agent 工作区的硬性流程
│   └── TOOLS_kuajing_section.md    # 环境与命令本机特定
├── docs/superpowers/          # 设计文档（spec + 实施计划）
│   ├── specs/                 #   设计文档
│   └── plans/                 #   实施计划（含每一轮计划缺陷修正记录）
├── assets/demo.mp4            # 60-90s 演示录屏
└── tools/gen_orders.py        # 一次性 mock 订单生成器（seed=42 可复现）
```

## 本地复现（不依赖飞书/腾讯云,跑离线评测）

```bash
git clone https://github.com/songhuichen7-jpg/agent_shop.git
cd agent_shop
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# 在 .env 里填 DEEPSEEK_API_KEY=sk-...（DeepSeek 官方 API key）

pytest -q                                            # 47 单测全绿
python eval/run_eval.py --which agent --limit 3      # 3 条小冒烟
python eval/run_eval.py --which agent    > eval/score_agent.json    # 全量 70 条 agent（~35s/条）
python eval/run_eval.py --which baseline > eval/score_baseline.json # 全量 70 条 baseline
```

单测覆盖：
- 数据完整性（政策 KB ≥6 类目；订单 6 状态全覆盖；测试集引用真实 clause_id/order_id）
- 各 src/ 模块单测（pipeline 编排、护栏、决策、查找）
- feishu_actions.sh 与 run_pipeline 副作用接线

## 线上部署（腾讯云 Lighthouse + 飞书 + OpenClaw）

完整步骤见 [`deploy/openclaw_server_deploy.sh`](deploy/openclaw_server_deploy.sh) 与 [`deploy/wire_agents_md.sh`](deploy/wire_agents_md.sh)。简要：

1. **腾讯云 Lighthouse**：AI Agent 分类一键部署 OpenClaw 模板（≥2核4G）。控制台 `http://公网IP:18789`。
2. **飞书自建应用**：开 IM + 事件订阅 + 多维表格(`base:*`) + 任务(`task:task`)权限并发版。
3. **OpenClaw 绑定**：控制台连飞书 channel + 绑 LLM（生产用 `deepseek-v4-flash`）。
4. **服务器上**：
   ```bash
   bash deploy/openclaw_server_deploy.sh prep      # 备份 + 加 agent_shop/runtime 卷
   bash deploy/openclaw_server_deploy.sh recreate  # 重建仅 gateway 容器
   bash deploy/openclaw_server_deploy.sh deps      # 持久卷安装 lark-cli (npm)
   bash deploy/openclaw_server_deploy.sh discover  # 读出 OpenClaw skill 注册路径
   ```
5. **lark-cli 飞书 Device Flow 授权**：容器内 `lark-cli config init` + `auth login --recommend`，浏览器点一次同意。凭据存到挂载的持久卷（`/home/node/runtime/larkhome`），容器重建不丢。
6. **接入 agent 工作区**：`bash deploy/wire_agents_md.sh apply`（幂等 sentinel 替换，workspace git 留还原点）→ `restart` 重建 gateway 让 AGENTS.md 生效。
7. **回滚**：`bash deploy/openclaw_server_deploy.sh rollback` 或 `bash deploy/wire_agents_md.sh rollback`。

> 部署纪律：仅动 `openclaw-agent-shop` 栈，绝不触碰共云的其他容器/卷/数据；每步 docker compose 操作前后核对邻栈 uptime。

## 方法论亮点（设计差异化）

1. **可核查 grounding**：回复每条事实句必须能追溯到 `[clause_id]` 引用或 `order_facts`；查不到依据宁可升级也不编造。引用命中率从 baseline 0% → 81%。
2. **不乱承诺护栏（带引用豁免）**：禁止"具体到货天数 / 具体赔付金额 / 保证清关"；但**带 `[政策条款]` 引用**的句子视为政策事实，不算 agent 私自承诺——既挡乱承诺又不误伤正常的政策引用。对抗集触发率 0%（baseline 8.3%）。
3. **规则化决策 + 边界鲁棒**：硬承诺/威胁/赔付/海关查扣/签收后报失 / 对账申诉 各有触发器；同时为"商家问"（不是"代赔"）等场景做了豁免，避免过度升级正常咨询。决策准确 84.3% 反超 baseline 81.4%，同时危险漏报降至 0。
4. **评测驱动**：先 r0 baseline → 诊断错误模式 → r1 收窄过宽触发 → r2 补三类边界。每轮 `pytest` 必须仍绿，对抗集 0 过度承诺为安全底线，不为提分牺牲。计划在 `docs/superpowers/plans/` 里有完整的 r0/r1/r2 缺陷与修复记录。
5. **跨 provider 可迁移**：同一规则层 + 数据 + 评测脚本，从 DeepSeek 切到小米 Mimo-v2-flash 同样成立（详见 [SCORECARD](eval/SCORECARD.md) "跨 provider" 节）。

## 范围与限制（诚实声明）

- **数据全合成**：政策条款 / 订单 / 客诉均虚构，不涉任何真实商户。
- **测试集 n=70** 较小；本作品的方法论与代码可工程化扩展，但生产部署需更广的真实/混合标注集再次验证。
- **决策层是规则化**：覆盖该 70 条评测集的常见模式很好，但极端长尾仍可能需要 LLM-judge fallback；当前规则错误模式可解释，便于运营迭代。
- **飞书任务默认不指派人**：设 `FEISHU_TASK_ASSIGNEE_ID` 可自动派给具体 open_id。
- **演示/研究用途**：本仓库是该问题域的技术探索与方法论验证，不适合直接用于生产承接真实商户客诉。

## 文档索引

- 设计文档：[`docs/superpowers/specs/2026-05-19-cross-border-complaint-agent-design.md`](docs/superpowers/specs/2026-05-19-cross-border-complaint-agent-design.md)
- 实施计划（含全部计划缺陷修正记录）：[`docs/superpowers/plans/2026-05-19-cross-border-complaint-agent.md`](docs/superpowers/plans/2026-05-19-cross-border-complaint-agent.md)
- 评测记分卡：[`eval/SCORECARD.md`](eval/SCORECARD.md)

## 作者

陈松辉（[songhuichen7@gmail.com](mailto:songhuichen7@gmail.com)） · GitHub: [@songhuichen7-jpg](https://github.com/songhuichen7-jpg)

## 许可

代码 MIT；数据全合成、仅供作品演示与评测复现；不对生产使用做任何保证。
