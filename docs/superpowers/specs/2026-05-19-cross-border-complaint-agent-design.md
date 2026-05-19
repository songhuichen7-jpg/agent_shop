# 跨境物流客诉自动处理 Agent — 设计文档（Spec）

- 日期：2026-05-19
- 状态：已与用户逐节确认，待用户复核本文档
- 工作名：`KuajingDesk`（可改）
- 项目目录：`/Users/veko/code/agent_shop`

---

## 1. 背景与目标

陈松辉（2026 应届，求职 AI 产品/应用方向）需要一个**旗舰作品集项目**，用于通过 AI 应用/业务落地类岗位（对标 BOSS 直聘 BUFFALO「AI+业务管培生」9-13K，跨境 B2C 物流）的投递筛选。

市场调研（2026-05-19）结论：

- 「AI 应用工程师 / AI Agent 开发」已成独立岗位大类，横跨多个传统行业，大量「经验不限/应届」。
- 这些 JD 不论 title 反复 gate 在同一件事：**一个能演示「用 AI 跑通真实业务流程 + 可量化效果」的案例**。BUFFALO 投递明确要求附「用 AI 工具解决真实问题的 1 个案例（≤100 字，截图/链接）」。
- 雇主点名当红 Agent 工具：**OpenClaw（=「小龙虾」，同一物）**、**飞书 CLI**。zhipin 上有岗位直接命名「AI应用工程师（OpenClaw）」。

作品集缺口：用户已有 2 个项目偏消费/金融（命理对话、金融研报）。本旗舰补 **B2B 企业业务流程自动化** 缺口，且建在雇主点名的工具上（非自研重系统）。

## 2. 用户与成功标准

- 主用户（作品受众）：跨境物流/电商类公司的 HR、业务负责人、AI 团队面试官。
- 成功标准 = 投递时可附的硬头条：
  > 在 60-80 条标注客诉测试集上：分类准确率 ≥X% · 升级判定准确率 ≥Y% ·「该升级却自动答」危险漏报单列 · **过度承诺（乱报时效/赔付）率 ≈ 0** · 单条人工 ~5 分钟 → Agent 秒级；对比裸 LLM 单 prompt baseline 提升 N%。
- 方法论一致性：复用用户 youshi.fun 招牌「可核查 + 必引依据 + 不下绝对承诺 + vs baseline 量化」，瘦身为一层薄护栏 + 小评测，作为差异化点缀，不是项目主体。

## 3. 范围

**做：**
- 一个自定义 OpenClaw Skill「跨境客诉助手」（核心交付物）
- 合成数据：双语政策 KB + mock 订单库 + 标注测试集
- 离线评测脚本 + 一页记分卡
- 飞书渠道演示（OpenClaw 接飞书）+ 飞书 CLI 写多维表格看板 / 建任务派单
- 演示录屏 + README + 一页纸投递案例

**明确不做（YAGNI 红线）：**
- 不接真实商户/真实订单系统（全合成）
- 不做账号体系/多租户/权限
- 不接真实 WMS/清关系统
- 不做模型微调
- 不铺多渠道（仅飞书演示；README 注明 OpenClaw 原生可扩展）
- 测试集 ≤80 条，不追 999 级
- 护栏只两道，不做研究级 verifier 家族
- 不做生产级监控/告警

## 4. 架构

**部署形态：** 腾讯云轻量服务器（Lighthouse）一键部署 OpenClaw（AI Agent 模板，荐 2核4G+），控制台 `http://公网IP:18789`；绑定飞书自建应用（配 `im:` 等权限并发版）。渠道 = 飞书。

**双工具闭环：**

```
跨境商户在【飞书】发消息（中/英/混）
   ▼
OpenClaw（腾讯云，小龙虾） ── 飞书 Channel ── 「跨境客服」Agent
   ▼  执行自定义 Skill「跨境客诉助手」
   ① 分类  ② 查单(mock 工具)  ③ 取政策据(grounded, 带 clause_id)
   ④ 起草中英双语回复  ⑤ 护栏(有据/不乱承诺)  ⑥ 决策
        │
        ├─[可自动答]→ 飞书回复商户
        │             └→ 飞书 CLI 写入飞书【多维表格】= 运营看板（自动解决率/类目分布）
        │
        └─[须升级]  → 飞书 CLI 建飞书【任务】@人工 + 附 Agent 初判与依据
```

职责边界：OpenClaw 扛多渠道收发与沙箱执行；飞书 CLI 负责「AI 真正操作企业系统」（写多维表格、建任务）；用户交付中间的 Skill + 数据 + 护栏 + 评测。OpenClaw Skill 与飞书 CLI 的具体规范/命令面以官方文档为准，实现时定型，不臆造。

**两个飞书集成面（须区分，可行性核实后明确）：**
- (a) **OpenClaw 飞书 channel**：与商户聊天的入站/出站，由 OpenClaw 内建 channel 适配器负责，配置在 OpenClaw 控制台，需飞书自建应用具备 IM + 事件订阅权限。
- (b) **飞书 CLI**：Skill 通过 `exec` 调 `lark-cli` 操作飞书数据（写多维表格看板行、建任务派单），需飞书应用具备 bitable + task + im 权限，并经一次性 `lark-cli auth login` OAuth 授权（凭据存 OS 密钥链，之后非交互可脚本化）。
- 建议 (a)(b) 用**同一个飞书自建应用**、并集权限，减少 P0 配置量。

## 5. 核心组件：Skill「跨境客诉助手」

本质 = 结构化 Skill 指令 + 2 个本地小工具 + 飞书 CLI 动作，不是编排引擎。

| 步 | 做什么 | 实现（轻） |
|---|---|---|
| ① 分类 | 类目 + 紧急度 + 语言 + 情绪 | LLM 按固定枚举输出 |
| ② 查单 | 订单/物流状态、关键时间、异常标记 | 本地工具 `order_lookup`（合成 JSON/SQLite） |
| ③ 取据 | 命中双语政策条款（带 `clause_id`） | 本地工具 `policy_lookup`（小政策文件，关键词/分节匹配） |
| ④ 起草 | 中英双语回复，每事实句挂 `[clause_id]` 或订单事实 | LLM，提示词强约束 |
| ⑤ 护栏 | 有据校验 + 不乱承诺校验 | 规则+LLM 自检；不过关→改写或转升级 |
| ⑥ 决策 | 可自动答 / 须升级 | 命中升级触发器即升级 |
| ⑦ 行动 | 自动答→飞书回复+写多维表格；升级→建飞书任务@人工 | 飞书 CLI |

**6 个类目：** 物流时效 / 丢件破损 / 费用与对账争议 / 清关问题 / 退件与拒收 / 一般咨询。

**升级触发器（写死、可解释）：** 涉赔付退款金额认定 · 无匹配政策条款或超范围 · 海关/法务/禁运 · 情绪极端或威胁差评/工单升级 · 订单查不到或查取置信低 · 需具体时效承诺待运营确认。

**输出契约（结构化 JSON，喂多维表格 + 供评测打分）：**
```json
{ "category": "...", "urgency": "...", "language": "...",
  "decision": "auto|escalate",
  "citations": ["clause_id..."], "order_facts": ["..."],
  "confidence": 0.0,
  "reply_zh": "...", "reply_en": "...",
  "escalate_reason": "..." }
```

## 6. 数据设计（全合成，不涉真实商户）

1. **政策/SOP 知识库**：双语 ~20-30 条，`{clause_id, category, zh, en}`。覆盖时效政策、丢件破损赔付、费用对账、清关与禁运、退件拒收、一般 FAQ。中国→南非 B2C 语境，规则数字全虚构。
2. **订单/物流 mock 库**：~200-400 单，`{order_id, merchant_id, 线路, status(在途/清关中/已签收/异常/退件/丢件), 时间戳, 轨迹, 异常标记}`，SQLite/JSON。
3. **客诉测试集**：~60-80 条带标注（LLM 生成 + 人工筛）。每条原始消息（中/英/混，语气各异）+ 金标 `gold_category / gold_decision / gold_citations / must_not_promise`。配比：多数可自动答、一批必须升级、少量对抗样本（诱导乱承诺）。

## 7. 评测与记分卡

离线跑测试集（不走实时飞书），对比「裸 LLM 单 prompt」baseline：

| 指标 | 说明 |
|---|---|
| 分类准确率 | |
| 升级判定准确率 | 含混淆矩阵，**「该升级却自动答」危险漏报单列** |
| 引用命中率 | 是否命中 gold 条款 |
| **过度承诺率** | 对抗子集触发率，目标 ≈0 ← 最亮差异化 |
| 处理耗时 | 人工 ~5min vs Agent 秒级 |
| vs baseline | 证明 Skill+护栏增量价值 |

产出：一页记分卡（终端表 + README 一张表）。这是投递「案例」硬数字来源。

**护栏细化（两道，轻）：**
- 有据校验：回复每个事实句必须映射到 `citation` 或 `order_fact`，否则不过。
- 不乱承诺：禁止「具体到货天数/日期、具体赔付金额、保证清关通过、无依据减免」——正则粗筛 + LLM 逐句自检（承诺/有据/无据）。
- 不过关：改写 1 次 → 仍不过 → 强制升级（宁可升级不编）。

## 8. 交付物 + 投递案例形态

1. 自定义 OpenClaw Skill「跨境客诉助手」（GitHub repo，按 Skill 规范打包）
2. 合成数据集（政策 KB + mock 订单 + ~60-80 测试集）
3. 离线评测脚本 + 一页记分卡
4. 60-90s 演示录屏：飞书来一条乱糟糟中英客诉 → 端到端处理 → 自动回复 + 多维表格看板加一行；再演示对抗/升级 → 建飞书任务 @人工
5. README（说明 + 架构图 + 头条指标 + 部署 + demo 链接）
6. 投递用一页纸案例（满足 BUFFALO「≤100 字 + 截图/链接」）

**投递 ≤100 字 钩子（模板，按真实数字填）：**
> 用 OpenClaw（小龙虾）+ 飞书 CLI 做了跨境物流客诉自动处理 Agent：飞书来一条中英混客诉 → 自动分类→查单→引政策条款起草双语回复→护栏拦乱承诺→可答即回复并写入飞书多维表格看板，该升级则建飞书任务派人工。60-80 条标注集：分类准确 X%、危险漏报 Y%、过度承诺≈0，单条 5 分钟→秒级。Repo+录屏：_链接_

## 9. 风险与缓解

| 风险 | 缓解 |
|---|---|
| 飞书自建应用权限审批/发版有摩擦 | P0 优先打通；腾讯云官方+菜鸟教程全程文档可循 |
| OpenClaw Skill 规范/飞书 CLI 命令面认知不全 | 不臆造，实现时对照 `larksuite/cli` 与 OpenClaw 官方文档定型 |
| 腾讯云一键模板版本与教程差异 | P0 以实际控制台为准，记录实际版本到 README |
| 合成对抗集质量决定「过度承诺率≈0」可信度 | 对抗样本人工精筛；记分卡注明样本来源与规模 |
| 范围蔓延（想做大评测/多渠道） | 第 3 节红线为硬约束，超出走后续迭代 |

## 10. 阶段拆分（供 writing-plans 出实施计划）

- **P0 环境**：腾讯云一键 OpenClaw + 飞书自建应用（并集权限）接通 channel + **OpenClaw 绑定国产模型（Kimi/百炼，见 §11）** + `npx @larksuite/cli@latest install` + `lark-cli config init` + `lark-cli auth login --recommend`（一次性 OAuth 人工授权）+ 冒烟验证闭环（`lark-cli im +messages-send` 发一条 + 写一行多维表格 + 建一个任务 + `lark-cli auth check`）；实际控制台版本与命令面记录进 README
- **P1 数据**：政策 KB + mock 订单 + 测试集 v1
- **P2 Skill v1**：分类→查单→取据→双语起草→输出契约（先无护栏打通）
- **P3 护栏+决策**：两道护栏 + 升级触发器 + 飞书 CLI 行动（回复/写多维表格/建任务）
- **P4 评测**：离线脚本 + baseline 对比 + 记分卡，按结果回调提示词/触发器
- **P5 交付**：演示录屏 + README + 一页纸投递案例

## 11. 可行性核实结论（2026-05-19）

**结论：架构可行，整体低风险，无需改设计。** 仅以下小幅细化与 1 项待定决策。

已核实：

- **OpenClaw 自定义 Skill 机制**（低风险）：Skill = 目录 `SKILL.md`（YAML frontmatter + Markdown 指令，必需）+ `scripts/`（确定性 Bash/Python，Agent 可直接执行不占上下文）+ `references/`（按需查阅，如政策 KB / 飞书 CLI 用法 / 升级规则）+ `assets/`。工具集成经 `web_search`/`web_fetch`/`exec`。本设计 1:1 映射：`scripts/`→`order_lookup`/`policy_lookup`/护栏/评测；`references/`→政策 KB+飞书 CLI 备忘+升级规则；`SKILL.md`→处理链编排；`exec`→调 `lark-cli`。即 Anthropic 风格 Skill 格式，用户已熟。
- **飞书 CLI 能力**（低风险）：`npx @larksuite/cli@latest install`；鉴权 app_id/secret + OAuth（`config init` / `auth login --recommend`，非交互模式输出授权链接给人点一次，凭据存 OS 密钥链）。发消息已确认 `lark-cli im +messages-send --chat-id "oc_xxx" --text "..."`；多维表格记录增改、任务建/查/改/完 均为官方能力（精确子命令以 `lark-cli <域> --help` 与官方文档 P0 定型）；`--format json/ndjson` 支持脚本化（满足 Skill `exec` 调用）。
- **OpenClaw↔飞书 + 腾讯云**（低风险）：腾讯云 Lighthouse 有 OpenClaw 一键模板（AI Agent 类，荐 2核4G+，控制台 `:18789`），飞书 channel 有「快速 QR 配置」与「手动自建应用（AppID/Secret + 事件订阅 + 权限 + 发版）」两条官方路径，文档充分。

细化（已并入 §4/§10，无需用户决策）：两个飞书集成面区分 + 单应用并集权限；P0 增一次性 `lark-cli auth login` 人工授权步；精确子命令 P0 定型。

**决策（已确认 2026-05-19）：LLM 绑定。** OpenClaw 模型无关。腾讯云大陆服务器出网到 Anthropic 不稳。**线上 OpenClaw 绑国产模型（Kimi/百炼）跑实时客诉**；**离线评测/开发用 Claude**（用户重度可用）保证记分卡质量。含义：护栏与提示词需在国产模型上验证（线上真实路径），评测记分卡注明"线上模型=国产、评测对照=Claude"，不混淆口径。

## 附：工具与版本参考（实现时以官方文档为准）

- OpenClaw（=「小龙虾」）：MIT 开源、本地优先 AI Agent 执行网关，接 50+ 渠道，Docker 沙箱，Skills 生态。
- 飞书 CLI `@larksuite/cli`：2026-03-28 开源，Go/npm/MIT；命令行调飞书开放平台 2500+ API（消息/文档/多维表格/任务等），为 AI Agent 设计，Claude Code/Cursor 支持。
- 腾讯云 Lighthouse：AI Agent 分类有 OpenClaw 一键模板，荐 2核4G+，控制台 `:18789`。

参考来源：
- 阿里云开发者社区《深度拆解 OpenClaw》 https://developer.aliyun.com/article/1715683
- Tencent Cloud techpedia《OpenClaw 详细介绍》 https://www.tencentcloud.com/techpedia/140976
- 飞书官网《飞书 CLI 安装与使用指南》 https://www.feishu.cn/content/article/7623291503305083853
- larksuite/cli GitHub https://github.com/larksuite/cli/blob/main/README.zh.md
- 腾讯云开发者社区《云上 OpenClaw 快速接入飞书指南》 https://cloud.tencent.com/developer/article/2626151
- 菜鸟教程《OpenClaw Skills — ClawHub》 https://www.runoob.com/ai-agent/openclaw-skills.html
- 腾讯云开发者社区《OpenClaw 自定义 Skill 开发踩坑全记录》 https://cloud.tencent.com/developer/article/2640166
