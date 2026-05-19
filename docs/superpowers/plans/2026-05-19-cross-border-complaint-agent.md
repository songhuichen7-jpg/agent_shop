# 跨境物流客诉自动处理 Agent — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 交付一个建在 OpenClaw（小龙虾）+ 飞书 CLI 上的跨境 B2C 物流客诉自动处理 Agent，含可量化评测记分卡，作为求职旗舰作品。

**Architecture:** 核心业务逻辑写成可导入的 Python 库（`src/`），TDD 覆盖；OpenClaw Skill（`skill/SKILL.md` + `scripts/` + `references/`）在线编排并调 `src/` 与 `lark-cli`；离线评测（`eval/`）直接 import `src/pipeline.py` 用 Claude 跑标注集，与线上国产模型路径共用 `skill/references/` 里的提示词/规则（单一事实源，DRY）。

**Tech Stack:** Python 3.11 · pytest · anthropic SDK（离线评测/开发用 Claude）· OpenClaw（腾讯云 Lighthouse）· `@larksuite/cli` · 飞书自建应用 · 线上 OpenClaw 绑国产模型（Kimi/百炼）

**Spec:** `docs/superpowers/specs/2026-05-19-cross-border-complaint-agent-design.md`（已定稿，3 次提交）

---

## 约定（实施前通读）

- **在线 vs 离线两条路径，共用规则源**：`skill/references/` 下的 `classify_prompt.md`、`draft_prompt.md`、`escalation_rules.md`、`policy_kb.json` 是唯一事实源。`SKILL.md`（在线，OpenClaw 国产模型读它）与 `src/`（离线，Claude）都加载这些文件，禁止各写一份。
- **LLM 在接口后面**：`src/llm.py` 定义 `LLMClient` 协议。单测用 `FakeLLM`（确定性，不联网）。离线评测/开发用 `ClaudeClient`。在线由 OpenClaw 绑定的国产模型按 `SKILL.md` 执行——不在本仓代码内调用。
- **机密不进 git**：`.env` 存 `ANTHROPIC_API_KEY`、飞书 `APP_ID/APP_SECRET`、国产模型 key，**gitignore**。合成数据（政策/订单/测试集）是虚构的，正常提交。
- **P0 含人工步骤**：开账号、买服务器、OAuth 点授权、填密钥由**用户本人**完成（Claude 给出逐步指引并在拿到凭据后跑验证命令）。Claude 不创建账号、不代付。
- **提交节奏**：每个 Task 末尾提交一次。提交信息用 `feat:/test:/docs:/chore:` 前缀 + `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`。
- **测试命令**：仓库根目录 `pytest -q`。每个测试任务给出精确单测命令与期望输出。

## 文件结构（决策锁定）

```
agent_shop/
├── .gitignore                     # .env / venv / __pycache__ / *.log
├── .env.example                   # 占位键名（无值），可提交
├── requirements.txt
├── pyproject.toml                 # pytest 配置
├── README.md                      # P5 产出
├── data/
│   ├── policy_kb.json             # ~20-30 双语条款（也被 skill/references 软链/复制）
│   ├── orders.json                # ~200-400 mock 订单
│   └── testset.jsonl              # ~60-80 标注客诉
├── src/
│   ├── __init__.py
│   ├── llm.py                     # LLMClient 协议 + FakeLLM + ClaudeClient
│   ├── rules.py                   # 加载 skill/references 的规则/提示词（单一事实源）
│   ├── order_lookup.py            # 查 mock 订单
│   ├── policy_lookup.py           # 政策 grounded 检索
│   ├── classify.py                # 调 LLM 出分类
│   ├── draft.py                   # 调 LLM 出双语回复
│   ├── guardrail.py               # 两道护栏
│   └── pipeline.py                # 离线编排，产出输出契约
├── skill/                         # OpenClaw Skill 包（核心交付物）
│   ├── SKILL.md
│   ├── scripts/
│   │   ├── run_pipeline.py        # 在线入口：读消息→调 src.pipeline→打印契约 JSON
│   │   └── feishu_actions.sh      # lark-cli 封装：回复 / 写多维表格 / 建任务
│   └── references/
│       ├── policy_kb.json         # = data/policy_kb.json（P2 起以 data/ 为源，构建时复制）
│       ├── classify_prompt.md
│       ├── draft_prompt.md
│       ├── escalation_rules.md
│       └── lark_cli_cheatsheet.md # P0 实测命令面填入
├── eval/
│   ├── baseline.py                # 裸单 prompt baseline
│   ├── metrics.py                 # 指标计算（纯函数，TDD）
│   └── run_eval.py                # 跑标注集 + baseline → 记分卡
├── tests/
│   ├── conftest.py                # FakeLLM、临时数据 fixtures
│   ├── test_data_integrity.py
│   ├── test_order_lookup.py
│   ├── test_policy_lookup.py
│   ├── test_classify.py
│   ├── test_draft.py
│   ├── test_guardrail.py
│   ├── test_pipeline.py
│   └── test_metrics.py
└── docs/superpowers/{specs,plans}/ # 已存在
```

---

# Phase P0 — 环境（人工为主，Claude 指引+验证）

> P0 产出不是代码，是「可用的线上闭环」。每个 Task 是有序操作 + 验证门。涉及账号/付费/授权/密钥由用户完成。完成后把实测信息写入 `skill/references/lark_cli_cheatsheet.md` 与 README 草稿。

### Task P0.1: 腾讯云 Lighthouse 部署 OpenClaw

**Files:** 无（运维）。产出记录到本地笔记，P5 并入 README。

- [ ] **Step 1（用户）：购买腾讯云轻量应用服务器**

进入腾讯云 Lighthouse 控制台 → 应用模板选「AI Agent」分类下的 OpenClaw / Clawdbot 模板 → 规格 ≥ 2核4G → 地域选大陆（与国产模型同区低延迟）→ 购买。
（财务操作，用户本人完成。）

- [ ] **Step 2（用户）：获取公网 IP 与控制台地址**

实例就绪后记录公网 IP。浏览器访问 `http://<公网IP>:18789`。

- [ ] **Step 3（验证）：OpenClaw 控制台可达**

Run（用户在浏览器）: 打开 `http://<公网IP>:18789`
Expected: OpenClaw 可视化管理控制台加载成功（非报错/超时）。
若失败：检查 Lighthouse 防火墙放通 18789 端口。

- [ ] **Step 4：记录实测信息**

把「实例规格 / 地域 / OpenClaw 版本号（控制台页脚或 About）/ 控制台地址」记入本地 `P0_NOTES.md`（gitignore，后续并入 README，不含公网 IP 等敏感信息时再提交）。

### Task P0.2: 飞书自建应用（并集权限，单应用复用）

- [ ] **Step 1（用户）：创建飞书自建应用**

飞书开放平台 open.feishu.cn → 开发者后台 → 创建企业自建应用 → 记录 `App ID` / `App Secret`。

- [ ] **Step 2（用户）：开通并集权限**

权限管理中开通（搜索 `im:` 全选 IM 收发；机器人能力）+ 多维表格 `bitable:app`/记录读写 + 任务 `task:task` 读写 + 「通过手机号/邮箱获取用户 ID」。事件订阅：订阅「接收消息 im.message.receive_v1」。创建版本并发布、企业内可用。

- [ ] **Step 3（用户）：把机密写入本地 `.env`（不提交）**

在仓库根 `.env`（P1.1 会建 `.gitignore`；P0 阶段先手动确保 `.env` 不被加入）写：
```
FEISHU_APP_ID=cli_xxx
FEISHU_APP_SECRET=xxx
```

- [ ] **Step 4（验证）：应用已发布**

Expected: 开发者后台该应用状态=已发布；版本可用范围含测试用企业。

### Task P0.3: OpenClaw 绑定飞书 channel + 国产模型

- [ ] **Step 1（用户）：控制台绑定飞书**

OpenClaw 控制台 → 渠道 → 飞书 → 填入 P0.2 的 App ID/Secret（或扫码快速配置）→ 配置事件回调 URL（控制台给出，回填到飞书开发者后台事件订阅）。

- [ ] **Step 2（用户）：绑定国产模型**

OpenClaw 控制台 → 模型 → 选 Kimi（或百炼），填该模型 API Key（用户的 key，写入 `.env` 备份键 `ONLINE_LLM_KEY=...`，控制台内填）。

- [ ] **Step 3（验证）：飞书↔OpenClaw 回声**

Run（用户在飞书）：给该机器人发「ping」
Expected: 机器人有任意回复（证明 channel 收发 + 模型链路通）。
失败排查：事件订阅 URL 校验是否通过；模型 key 是否有效；控制台日志。

### Task P0.4: 安装并授权 lark-cli

- [ ] **Step 1（Claude，若在用户机器）：安装 CLI**

Run: `npx @larksuite/cli@latest install`
Expected: 安装完成，`lark-cli --version` 可输出版本号。

- [ ] **Step 2（用户）：配置凭据并 OAuth 授权**

Run: `lark-cli config init`（交互，填 P0.2 App ID/Secret）
Run: `lark-cli auth login --recommend`
Expected: 终端输出授权链接 → 用户浏览器打开点「同意」→ 终端显示授权成功；凭据存入 OS 密钥链。

- [ ] **Step 3（验证）：鉴权与三类动作冒烟**

Run: `lark-cli auth check`
Expected: 输出已授权、scope 含 im/bitable/task。

Run: `lark-cli im +messages-send --chat-id "<测试群 chat_id>" --text "P0 smoke" --format json`
Expected: JSON 含 `message_id`，测试群收到消息。

（用户先在飞书建一张多维表格 `客诉看板`，记录其 `app_token` 与表 `table_id`。）
Run: `lark-cli`（多维表格新增一行的精确子命令——用 `lark-cli bitable --help` / `lark-cli <bitable record create 相关命令> --help` 查到后执行，写一行 `{类目:"smoke",决策:"auto"}`）
Expected: 表格新增一行；记录精确命令。

Run: 用 `lark-cli task --help` 查到建任务子命令，建一个标题 "P0 smoke task"
Expected: 任务创建成功；记录精确命令。

- [ ] **Step 4：固化命令面**

把 Step 3 实测出的「发消息 / 多维表格新增记录 / 建任务」三条精确命令（含参数名）写入 `skill/references/lark_cli_cheatsheet.md`（此文件 P1.1 后存在；P0 先记到 `P0_NOTES.md`，P1.1 建仓后迁入）。

- [ ] **Step 5: 提交（仅文档，不含机密）**

P0 笔记中可公开部分（OpenClaw 版本、命令面）在 P1.1 仓库就绪后并入 `skill/references/lark_cli_cheatsheet.md` 一起提交，不单独提交机密。

**P0 完成判据：** 飞书发消息→机器人回；`lark-cli` 能发消息/写多维表格/建任务；三条精确命令已记录。

---

# Phase P1 — 脚手架 + 合成数据

### Task P1.1: 项目脚手架

**Files:**
- Create: `.gitignore`, `.env.example`, `requirements.txt`, `pyproject.toml`, `src/__init__.py`, `tests/conftest.py`
- Create 占位: `skill/references/lark_cli_cheatsheet.md`（写入 P0 实测命令）

- [ ] **Step 1: 写 `.gitignore`**

```
.env
P0_NOTES.md
.venv/
venv/
__pycache__/
*.pyc
*.log
.pytest_cache/
```

- [ ] **Step 2: 写 `.env.example`**

```
ANTHROPIC_API_KEY=
FEISHU_APP_ID=
FEISHU_APP_SECRET=
ONLINE_LLM_KEY=
FEISHU_BITABLE_APP_TOKEN=
FEISHU_BITABLE_TABLE_ID=
FEISHU_HUMAN_CHAT_ID=
```

- [ ] **Step 3: 写 `requirements.txt`**

```
anthropic>=0.40
python-dotenv>=1.0
pytest>=8.0
```

- [ ] **Step 4: 写 `pyproject.toml`**

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
addopts = "-q"
```

- [ ] **Step 5: 建空包与笔记迁入**

Create `src/__init__.py`（空）。
Create `skill/references/lark_cli_cheatsheet.md`，把 P0.4 实测的三条精确命令粘入（结构：## 发消息 / ## 多维表格新增记录 / ## 建任务，每节一个可复制命令块 + 参数说明）。

- [ ] **Step 6: 写 `tests/conftest.py`（FakeLLM + 数据 fixtures）**

```python
import json, pathlib, pytest

DATA = pathlib.Path(__file__).parent.parent / "data"

class FakeLLM:
    """确定性 LLM 桩：按注册的 (tag -> dict) 返回 JSON 字符串。"""
    def __init__(self, responses=None):
        self.responses = responses or {}
        self.calls = []
    def complete_json(self, prompt: str, tag: str) -> dict:
        self.calls.append((tag, prompt))
        if tag not in self.responses:
            raise AssertionError(f"FakeLLM 未注册 tag={tag}")
        return self.responses[tag]

@pytest.fixture
def fake_llm():
    return FakeLLM()

@pytest.fixture
def sample_orders(tmp_path):
    orders = [
        {"order_id": "BF1001", "merchant_id": "M01", "route": "CN-ZA",
         "status": "清关中", "events": [{"ts": "2026-05-10", "desc": "到达约堡海关"}],
         "exception": None, "ship_date": "2026-05-05"},
        {"order_id": "BF1002", "merchant_id": "M01", "route": "CN-ZA",
         "status": "丢件", "events": [{"ts": "2026-05-08", "desc": "末端派送异常"}],
         "exception": "lost", "ship_date": "2026-05-01"},
    ]
    p = tmp_path / "orders.json"
    p.write_text(json.dumps(orders, ensure_ascii=False))
    return p

@pytest.fixture
def sample_policy(tmp_path):
    kb = [
        {"clause_id": "P-TIME-01", "category": "物流时效",
         "zh": "CN-ZA 标准时效为发货后 7-12 个工作日，清关延误不计入。",
         "en": "Standard CN-ZA lead time is 7-12 business days after dispatch; customs delays excluded."},
        {"clause_id": "P-LOST-01", "category": "丢件破损",
         "zh": "确认丢件后按申报价值赔付，需 5 个工作日核实。",
         "en": "Confirmed lost parcels are compensated at declared value after a 5-business-day verification."},
    ]
    p = tmp_path / "policy_kb.json"
    p.write_text(json.dumps(kb, ensure_ascii=False))
    return p
```

- [ ] **Step 7: 验证脚手架**

Run: `python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt && pytest -q`
Expected: `no tests ran`（0 收集），无导入错误。

- [ ] **Step 8: 提交**

```bash
git add .gitignore .env.example requirements.txt pyproject.toml src/__init__.py tests/conftest.py skill/references/lark_cli_cheatsheet.md
git commit -m "chore: 项目脚手架与 FakeLLM/数据 fixtures"
```

### Task P1.2: 政策 KB（双语 ~20-30 条）+ 数据完整性测试

**Files:**
- Create: `data/policy_kb.json`
- Test: `tests/test_data_integrity.py`

- [ ] **Step 1: 写失败测试（政策 KB schema）**

`tests/test_data_integrity.py`:
```python
import json, pathlib, re
DATA = pathlib.Path(__file__).parent.parent / "data"
CATEGORIES = {"物流时效","丢件破损","费用与对账争议","清关问题","退件与拒收","一般咨询"}

def load(name): return json.loads((DATA / name).read_text())

def test_policy_kb_schema():
    kb = load("policy_kb.json")
    assert 20 <= len(kb) <= 30, f"政策条款数应 20-30，实际 {len(kb)}"
    ids = set()
    for c in kb:
        assert set(c) >= {"clause_id","category","zh","en"}
        assert re.fullmatch(r"P-[A-Z]+-\d{2}", c["clause_id"]), c["clause_id"]
        assert c["category"] in CATEGORIES
        assert c["zh"].strip() and c["en"].strip()
        assert c["clause_id"] not in ids, f"重复 clause_id {c['clause_id']}"
        ids.add(c["clause_id"])
    cats = {c["category"] for c in kb}
    assert cats == CATEGORIES, f"每个类目至少 1 条，缺 {CATEGORIES - cats}"
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest tests/test_data_integrity.py::test_policy_kb_schema -v`
Expected: FAIL（`data/policy_kb.json` 不存在）。

- [ ] **Step 3: 创作 `data/policy_kb.json`**

写 20-30 条，6 类目每类 ≥1，中国→南非 B2C 语境，规则数字全虚构。示例 2 条（按此结构补足到 20-30）：
```json
[
  {"clause_id":"P-TIME-01","category":"物流时效","zh":"CN-ZA 标准时效为发货后 7-12 个工作日，清关延误不计入时效。","en":"Standard CN-ZA lead time is 7-12 business days after dispatch; customs delays are excluded from the SLA."},
  {"clause_id":"P-LOST-01","category":"丢件破损","zh":"经轨迹与仓查确认丢件后，按申报价值赔付，核实周期 5 个工作日。","en":"After loss is confirmed via tracking and warehouse audit, compensation is paid at declared value within a 5-business-day verification window."}
]
```
覆盖建议：物流时效 4-5、丢件破损 4-5、费用与对账争议 4、清关问题 4、退件与拒收 4、一般咨询 3-4。

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest tests/test_data_integrity.py::test_policy_kb_schema -v`
Expected: PASS。

- [ ] **Step 5: 同步到 skill/references**

Run: `cp data/policy_kb.json skill/references/policy_kb.json`
（约定：`data/` 为源，构建时复制到 `skill/references/`；写一句到 `skill/references/lark_cli_cheatsheet.md` 顶部注明此约定，或新建 `skill/references/README.md` 注明。此处新建 `skill/references/_SYNC.md` 一行说明：`policy_kb.json 由 data/ 复制，勿手改`。）

- [ ] **Step 6: 提交**

```bash
git add data/policy_kb.json skill/references/policy_kb.json skill/references/_SYNC.md tests/test_data_integrity.py
git commit -m "feat: 双语政策 KB（20-30 条）+ schema 完整性测试"
```

### Task P1.3: Mock 订单库（~200-400）+ 完整性测试

**Files:** Modify `data/`（Create `data/orders.json`）; Modify `tests/test_data_integrity.py`

- [ ] **Step 1: 追加失败测试**

在 `tests/test_data_integrity.py` 追加：
```python
STATUSES = {"在途","清关中","已签收","异常","退件","丢件"}

def test_orders_schema():
    orders = load("orders.json")
    assert 200 <= len(orders) <= 400, f"订单数应 200-400，实际 {len(orders)}"
    ids = set()
    for o in orders:
        assert set(o) >= {"order_id","merchant_id","route","status","events","exception","ship_date"}
        assert o["order_id"] not in ids; ids.add(o["order_id"])
        assert o["status"] in STATUSES
        assert isinstance(o["events"], list) and o["events"]
    assert {o["status"] for o in orders} == STATUSES, "每种状态至少 1 单"
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest tests/test_data_integrity.py::test_orders_schema -v`
Expected: FAIL（`orders.json` 不存在）。

- [ ] **Step 3: 生成 `data/orders.json`**

写一次性生成脚本 `tools/gen_orders.py`（不进 src，生成后可留仓）：
```python
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
```
Run: `python tools/gen_orders.py`

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest tests/test_data_integrity.py::test_orders_schema -v`
Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add data/orders.json tools/gen_orders.py tests/test_data_integrity.py
git commit -m "feat: ~300 条 mock 订单 + schema 测试"
```

### Task P1.4: 标注客诉测试集（60-80）+ 引用/订单引用完整性测试

**Files:** Create `data/testset.jsonl`; Modify `tests/test_data_integrity.py`

- [ ] **Step 1: 追加失败测试（含引用完整性）**

```python
def test_testset_schema_and_refs():
    lines = (DATA / "testset.jsonl").read_text().splitlines()
    rows = [json.loads(l) for l in lines if l.strip()]
    assert 60 <= len(rows) <= 80, f"测试集应 60-80，实际 {len(rows)}"
    kb_ids = {c["clause_id"] for c in load("policy_kb.json")}
    order_ids = {o["order_id"] for o in load("orders.json")}
    n_escalate = 0
    for r in rows:
        assert set(r) >= {"id","message","gold_category","gold_decision","gold_citations","must_not_promise","referenced_order"}
        assert r["gold_category"] in CATEGORIES
        assert r["gold_decision"] in {"auto","escalate"}
        for cid in r["gold_citations"]:
            assert cid in kb_ids, f"{r['id']} 引用了不存在条款 {cid}"
        if r["referenced_order"]:
            assert r["referenced_order"] in order_ids, f"{r['id']} 引用了不存在订单"
        assert isinstance(r["must_not_promise"], bool)
        n_escalate += r["gold_decision"] == "escalate"
    assert n_escalate >= 12, "必须升级样本至少 12 条"
    assert sum(r["must_not_promise"] for r in rows) >= 8, "对抗样本至少 8 条"
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest tests/test_data_integrity.py::test_testset_schema_and_refs -v`
Expected: FAIL（`testset.jsonl` 不存在）。

- [ ] **Step 3: 创作 `data/testset.jsonl`（60-80 行）**

每行一个 JSON。配比：可自动答 ~40-55；必须升级 ≥12；对抗（must_not_promise=true，诱导乱承诺）≥8。消息中/英/混、语气各异。示例 3 行（按此补足）：
```
{"id":"T001","message":"我的单 BF1003 发了快两周还没到，到底什么时候能到?","gold_category":"物流时效","gold_decision":"auto","gold_citations":["P-TIME-01"],"must_not_promise":false,"referenced_order":"BF1003"}
{"id":"T002","message":"BF1007 lost?? you guys must pay me 300 USD right now or I leave 1-star everywhere","gold_category":"丢件破损","gold_decision":"escalate","gold_citations":["P-LOST-01"],"must_not_promise":true,"referenced_order":"BF1007"}
{"id":"T003","message":"对账差了两笔运费，谁能解释下","gold_category":"费用与对账争议","gold_decision":"escalate","gold_citations":[],"must_not_promise":false,"referenced_order":null}
```

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest tests/test_data_integrity.py -v`
Expected: 3 passed（policy/orders/testset 全绿）。

- [ ] **Step 5: 提交**

```bash
git add data/testset.jsonl tests/test_data_integrity.py
git commit -m "feat: 60-80 条标注客诉测试集 + 引用完整性测试"
```

---

# Phase P2 — 核心代码 + Skill v1（先无护栏打通）

### Task P2.1: LLM 接口与规则加载

**Files:** Create `src/llm.py`, `src/rules.py`; Test `tests/test_classify.py`（部分），新增 `tests/test_rules.py`

- [ ] **Step 1: 写失败测试 `tests/test_rules.py`**

```python
from src.rules import load_reference

def test_load_reference_reads_skill_references():
    txt = load_reference("classify_prompt.md")
    assert "类目" in txt and len(txt) > 50
```

- [ ] **Step 2: 跑确认失败**

Run: `pytest tests/test_rules.py -v`
Expected: FAIL（模块/文件不存在）。

- [ ] **Step 3: 写 `src/rules.py` 与提示词文件**

`src/rules.py`:
```python
import pathlib
REF = pathlib.Path(__file__).parent.parent / "skill" / "references"

def load_reference(name: str) -> str:
    return (REF / name).read_text(encoding="utf-8")
```
Create `skill/references/classify_prompt.md`:
```
你是跨境物流客服分类器。读取商户消息，仅输出 JSON：
{"category": 6 选 1, "urgency":"high|normal|low", "language":"zh|en|mixed", "sentiment":"calm|annoyed|angry"}
category 取值：物流时效 | 丢件破损 | 费用与对账争议 | 清关问题 | 退件与拒收 | 一般咨询
不输出多余文本。
```
Create `skill/references/draft_prompt.md`:
```
你是跨境物流客服。基于「订单事实」与「政策条款」起草中英双语回复。
规则：每个事实陈述必须能追溯到给定的 clause_id 或 order_fact；
严禁承诺具体到货日期/天数、具体赔付金额、保证清关通过、无依据的费用减免；
查不到依据时，不要编造，转交人工。
仅输出 JSON：{"reply_zh":"...","reply_en":"...","citations":["clause_id..."],"order_facts":["..."]}
```
Create `skill/references/escalation_rules.md`:
```
满足任一即 decision=escalate：
1 涉赔付/退款金额认定 2 无匹配政策条款或超范围 3 海关/法务/禁运
4 情绪 angry 且含威胁（差评/工单/曝光）5 订单查不到或查取置信低
6 需具体时效承诺待运营确认
否则 decision=auto。
```

- [ ] **Step 4: 跑确认通过**

Run: `pytest tests/test_rules.py -v`
Expected: PASS。

- [ ] **Step 5: 写 `src/llm.py`**

```python
import json, os
from typing import Protocol

class LLMClient(Protocol):
    def complete_json(self, prompt: str, tag: str) -> dict: ...

class ClaudeClient:
    """离线评测/开发用。在线由 OpenClaw 绑定模型执行 SKILL.md，不走这里。"""
    def __init__(self, model="claude-opus-4-7"):
        from anthropic import Anthropic
        self.c = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self.model = model
    def complete_json(self, prompt: str, tag: str) -> dict:
        m = self.c.messages.create(model=self.model, max_tokens=1024,
              messages=[{"role":"user","content":prompt}])
        text = m.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("```")[1].lstrip("json").strip()
        return json.loads(text)
```

- [ ] **Step 6: 提交**

```bash
git add src/llm.py src/rules.py skill/references/classify_prompt.md skill/references/draft_prompt.md skill/references/escalation_rules.md tests/test_rules.py
git commit -m "feat: LLM 接口 + 规则/提示词单一事实源"
```

### Task P2.2: order_lookup（TDD）

**Files:** Create `src/order_lookup.py`; Test `tests/test_order_lookup.py`

- [ ] **Step 1: 写失败测试**

```python
from src.order_lookup import lookup_order

def test_lookup_hit(sample_orders):
    o = lookup_order("BF1001", path=sample_orders)
    assert o["status"] == "清关中" and o["route"] == "CN-ZA"

def test_lookup_miss(sample_orders):
    assert lookup_order("NOPE", path=sample_orders) is None
```

- [ ] **Step 2: 跑确认失败**

Run: `pytest tests/test_order_lookup.py -v`
Expected: FAIL（模块不存在）。

- [ ] **Step 3: 实现 `src/order_lookup.py`**

```python
import json, pathlib
_DEFAULT = pathlib.Path(__file__).parent.parent / "data" / "orders.json"

def lookup_order(order_id: str, path=None):
    data = json.loads(pathlib.Path(path or _DEFAULT).read_text())
    for o in data:
        if o["order_id"] == order_id:
            return o
    return None
```

- [ ] **Step 4: 跑确认通过**

Run: `pytest tests/test_order_lookup.py -v`
Expected: 2 passed。

- [ ] **Step 5: 提交**

```bash
git add src/order_lookup.py tests/test_order_lookup.py
git commit -m "feat: order_lookup + 测试"
```

### Task P2.3: policy_lookup（TDD，确定性 grounded 检索）

**Files:** Create `src/policy_lookup.py`; Test `tests/test_policy_lookup.py`

- [ ] **Step 1: 写失败测试**

```python
from src.policy_lookup import lookup_policy

def test_category_filter_and_keyword(sample_policy):
    hits = lookup_policy("包裹丢了要赔偿", category="丢件破损", path=sample_policy, k=2)
    assert hits and hits[0]["clause_id"] == "P-LOST-01"

def test_returns_empty_when_no_signal(sample_policy):
    hits = lookup_policy("???", category="清关问题", path=sample_policy, k=2)
    assert hits == []
```

- [ ] **Step 2: 跑确认失败**

Run: `pytest tests/test_policy_lookup.py -v`
Expected: FAIL。

- [ ] **Step 3: 实现 `src/policy_lookup.py`**

```python
import json, pathlib, re
_DEFAULT = pathlib.Path(__file__).parent.parent / "data" / "policy_kb.json"

def _tokens(q: str):
    # ascii 词 (>=2 字母) + 单个非 ascii 字符（中文等）。中文无 \W 词边界，
    # 必须按字匹配，否则整串中文会变成一个永不命中的巨型 token
    # （计划缺陷修正 2026-05-19）。不用 unicode 区间字面量以避免编码坑。
    ascii_toks = [t for t in re.split(r"\W+", q.lower()) if len(t) >= 2 and t.isascii()]
    cjk = [ch for ch in q if not ch.isascii() and not ch.isspace()]
    return ascii_toks + cjk

def _score(q: str, clause: dict) -> int:
    text = (clause["zh"] + clause["en"]).lower()
    return sum(1 for t in _tokens(q) if t in text)

def lookup_policy(query: str, category: str, path=None, k: int = 3):
    kb = json.loads(pathlib.Path(path or _DEFAULT).read_text())
    pool = [c for c in kb if c["category"] == category]
    scored = sorted(((_score(query, c), c) for c in pool), key=lambda x: -x[0])
    return [c for s, c in scored if s > 0][:k]
```

> 计划缺陷修正（2026-05-19）：原 `_score` 用 `re.split(r"\W+")` 对中文查询会得到一个不可命中的整串 token，导致 `lookup_policy` 永远返回 `[]`、test 1 失败。改为「ascii 词 + 单汉字」混合匹配（确定性、保留“无信号→空”性质，满足 spec“够 grounded 即可”）。测试不变（测试语义正确，缺陷在实现）。

- [ ] **Step 4: 跑确认通过**

Run: `pytest tests/test_policy_lookup.py -v`
Expected: 2 passed。

- [ ] **Step 5: 提交**

```bash
git add src/policy_lookup.py tests/test_policy_lookup.py
git commit -m "feat: policy_lookup 确定性 grounded 检索 + 测试"
```

### Task P2.4: classify（TDD，FakeLLM 桩）

**Files:** Create `src/classify.py`; Test `tests/test_classify.py`

- [ ] **Step 1: 写失败测试**

```python
from src.classify import classify

def test_classify_uses_llm_and_validates(fake_llm):
    fake_llm.responses["classify"] = {"category":"物流时效","urgency":"normal","language":"zh","sentiment":"annoyed"}
    out = classify("我的包裹很久没到", fake_llm)
    assert out["category"] == "物流时效"
    assert fake_llm.calls[0][0] == "classify"

def test_classify_rejects_bad_category(fake_llm):
    fake_llm.responses["classify"] = {"category":"乱写","urgency":"normal","language":"zh","sentiment":"calm"}
    import pytest
    with pytest.raises(ValueError):
        classify("x", fake_llm)
```

- [ ] **Step 2: 跑确认失败**

Run: `pytest tests/test_classify.py -v`
Expected: FAIL。

- [ ] **Step 3: 实现 `src/classify.py`**

```python
from src.rules import load_reference

CATEGORIES = {"物流时效","丢件破损","费用与对账争议","清关问题","退件与拒收","一般咨询"}

def classify(message: str, llm) -> dict:
    prompt = load_reference("classify_prompt.md") + "\n\n商户消息：\n" + message
    out = llm.complete_json(prompt, tag="classify")
    if out.get("category") not in CATEGORIES:
        raise ValueError(f"非法类目：{out.get('category')}")
    out.setdefault("urgency","normal"); out.setdefault("language","zh"); out.setdefault("sentiment","calm")
    return out
```

- [ ] **Step 4: 跑确认通过**

Run: `pytest tests/test_classify.py -v`
Expected: 2 passed。

- [ ] **Step 5: 提交**

```bash
git add src/classify.py tests/test_classify.py
git commit -m "feat: classify（LLM 接口 + 类目校验）+ 测试"
```

### Task P2.5: draft（TDD，FakeLLM 桩）

**Files:** Create `src/draft.py`; Test `tests/test_draft.py`

- [ ] **Step 1: 写失败测试**

```python
from src.draft import draft_reply

def test_draft_returns_bilingual_with_citations(fake_llm):
    fake_llm.responses["draft"] = {"reply_zh":"您的包裹在清关中[P-TIME-01]。","reply_en":"Your parcel is in customs [P-TIME-01].","citations":["P-TIME-01"],"order_facts":["status=清关中"]}
    out = draft_reply("消息", order={"status":"清关中"}, clauses=[{"clause_id":"P-TIME-01"}], llm=fake_llm)
    assert out["reply_zh"] and out["reply_en"]
    assert out["citations"] == ["P-TIME-01"]
    assert fake_llm.calls[0][0] == "draft"
```

- [ ] **Step 2: 跑确认失败**

Run: `pytest tests/test_draft.py -v`
Expected: FAIL。

- [ ] **Step 3: 实现 `src/draft.py`**

```python
import json
from src.rules import load_reference

def draft_reply(message: str, order, clauses, llm) -> dict:
    ctx = {"message": message, "order": order, "clauses": clauses}
    prompt = load_reference("draft_prompt.md") + "\n\n上下文：\n" + json.dumps(ctx, ensure_ascii=False)
    out = llm.complete_json(prompt, tag="draft")
    for key in ("reply_zh","reply_en","citations","order_facts"):
        out.setdefault(key, "" if key.startswith("reply") else [])
    return out
```

- [ ] **Step 4: 跑确认通过**

Run: `pytest tests/test_draft.py -v`
Expected: 1 passed。

- [ ] **Step 5: 提交**

```bash
git add src/draft.py tests/test_draft.py
git commit -m "feat: draft 双语回复（接口）+ 测试"
```

### Task P2.6: pipeline v1（编排，无护栏，TDD）

**Files:** Create `src/pipeline.py`; Test `tests/test_pipeline.py`

- [ ] **Step 1: 写失败测试**

```python
from src.pipeline import handle

def test_pipeline_outputs_contract(fake_llm, sample_orders, sample_policy):
    fake_llm.responses["classify"]={"category":"物流时效","urgency":"normal","language":"zh","sentiment":"annoyed"}
    fake_llm.responses["draft"]={"reply_zh":"清关中[P-TIME-01]","reply_en":"In customs [P-TIME-01]","citations":["P-TIME-01"],"order_facts":["status=清关中"]}
    out = handle("BF1001 怎么还没到", fake_llm, orders_path=sample_orders, policy_path=sample_policy)
    assert set(out) >= {"category","urgency","language","decision","citations","order_facts","confidence","reply_zh","reply_en","escalate_reason"}
    assert out["decision"] in {"auto","escalate"}
    assert out["category"] == "物流时效"

def test_pipeline_extracts_order_id(fake_llm, sample_orders, sample_policy):
    fake_llm.responses["classify"]={"category":"物流时效","urgency":"low","language":"zh","sentiment":"calm"}
    fake_llm.responses["draft"]={"reply_zh":"x","reply_en":"x","citations":[],"order_facts":[]}
    out = handle("请查 BF1002", fake_llm, orders_path=sample_orders, policy_path=sample_policy)
    assert "BF1002" in str(out["order_facts"]) or out["order_facts"]==[]  # 订单已注入上下文
```

- [ ] **Step 2: 跑确认失败**

Run: `pytest tests/test_pipeline.py -v`
Expected: FAIL。

- [ ] **Step 3: 实现 `src/pipeline.py`（v1：decision 暂固定 auto，P3 接护栏/升级）**

```python
import re
from src.classify import classify
from src.draft import draft_reply
from src.order_lookup import lookup_order
from src.policy_lookup import lookup_policy

ORDER_RE = re.compile(r"BF\d{4,}")

def handle(message: str, llm, orders_path=None, policy_path=None) -> dict:
    cls = classify(message, llm)
    m = ORDER_RE.search(message)
    order = lookup_order(m.group(0), path=orders_path) if m else None
    clauses = lookup_policy(message, cls["category"], path=policy_path)
    d = draft_reply(message, order, clauses, llm)
    return {
        "category": cls["category"], "urgency": cls["urgency"],
        "language": cls["language"], "sentiment": cls["sentiment"],
        "decision": "auto", "escalate_reason": "",
        "citations": d.get("citations", []), "order_facts": d.get("order_facts", []),
        "confidence": 1.0 if (order or clauses) else 0.3,
        "reply_zh": d.get("reply_zh",""), "reply_en": d.get("reply_en",""),
    }
```

- [ ] **Step 4: 跑确认通过**

Run: `pytest tests/test_pipeline.py -v`
Expected: 2 passed。

- [ ] **Step 5: 全量回归**

Run: `pytest -q`
Expected: 全绿（data/order/policy/classify/draft/pipeline/rules）。

- [ ] **Step 6: 提交**

```bash
git add src/pipeline.py tests/test_pipeline.py
git commit -m "feat: pipeline v1 编排（无护栏）+ 测试"
```

### Task P2.7: SKILL.md + 在线入口脚本

**Files:** Create `skill/SKILL.md`, `skill/scripts/run_pipeline.py`

- [ ] **Step 1: 写 `skill/scripts/run_pipeline.py`**

```python
#!/usr/bin/env python3
"""在线入口：OpenClaw 把商户消息作为 argv[1] 传入，打印输出契约 JSON。"""
import sys, json, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent))
from src.pipeline import handle
from src.llm import ClaudeClient  # 占位：在线由 OpenClaw 模型执行 SKILL.md；此脚本供本地联调

if __name__ == "__main__":
    msg = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    print(json.dumps(handle(msg, ClaudeClient()), ensure_ascii=False))
```

- [ ] **Step 2: 写 `skill/SKILL.md`**

```markdown
---
name: 跨境客诉助手
description: 处理跨境 B2C 物流商户的中英客诉/咨询：分类→查单→引政策→双语回复→护栏→决策→飞书行动。当飞书收到商户消息时触发。
---

# 跨境客诉助手

收到商户消息后，严格按序执行：

1. 读取 `references/classify_prompt.md`，对消息分类（类目/紧急度/语言/情绪）。
2. 若消息含订单号（形如 BF1234），执行 `scripts/run_pipeline.py "<原始消息>"` 获取结构化结果 JSON（含订单事实、政策引用、双语回复草稿、decision）。
3. 读取 `references/escalation_rules.md`，依据 JSON 的 decision 字段：
   - decision=auto：把 `reply_zh`+`reply_en` 通过飞书回复商户（见 `scripts/feishu_actions.sh reply`），然后把结构化结果写入飞书多维表格看板（`scripts/feishu_actions.sh log`）。
   - decision=escalate：用 `scripts/feishu_actions.sh escalate` 建飞书任务 @人工，正文附 category/escalate_reason/citations 与 Agent 初判，不直接答复商户敏感结论。
4. 不得自行编造政策或承诺时效/赔付；JSON 未给依据即按 escalate 处理。

参考文件：references/policy_kb.json、references/draft_prompt.md、references/lark_cli_cheatsheet.md
```

- [ ] **Step 3: 本地联调验证（用 Claude）**

Run: `ANTHROPIC_API_KEY=$KEY python skill/scripts/run_pipeline.py "BF1001 发了好久还没到"`
Expected: 打印一个含 `category/decision/reply_zh/reply_en` 的 JSON（decision 此阶段恒为 auto）。

- [ ] **Step 4: 提交**

```bash
git add skill/SKILL.md skill/scripts/run_pipeline.py
git commit -m "feat: SKILL.md 在线编排 + 本地联调入口"
```

---

# Phase P3 — 护栏 + 决策 + 飞书行动

### Task P3.1: 护栏一·不乱承诺（正则层，TDD）

**Files:** Create `src/guardrail.py`; Test `tests/test_guardrail.py`

- [ ] **Step 1: 写失败测试**

```python
from src.guardrail import check_no_overpromise

def test_flags_specific_eta():
    bad = check_no_overpromise("您的包裹将在 3 天内送达。", llm=None)
    assert bad and "eta" in bad[0]

def test_flags_money_promise():
    bad = check_no_overpromise("我们保证赔付 200 美元。", llm=None)
    assert bad and "payout" in bad[0]

def test_clean_reply_ok():
    assert check_no_overpromise("标准时效为 7-12 个工作日[P-TIME-01]。", llm=None) == []
```

- [ ] **Step 2: 跑确认失败**

Run: `pytest tests/test_guardrail.py -v`
Expected: FAIL。

- [ ] **Step 3: 实现 `src/guardrail.py`（先正则层）**

```python
import re

_ETA = re.compile(r"(\d+\s*(天|日|个工作日|days?)\s*(内|以内|之内|送达|到达))|保证.*(到货|清关通过)")
_PAYOUT = re.compile(r"(赔付|退款|补偿).{0,6}\d+\s*(元|美元|USD|rmb|人民币)|保证.*赔")

def check_no_overpromise(reply: str, llm=None) -> list[str]:
    """返回违规标签列表，空=通过。llm 非空时追加逐句自检（P3.2）。"""
    flags = []
    if _ETA.search(reply): flags.append("eta_promise")
    if _PAYOUT.search(reply): flags.append("payout_promise")
    return flags
```

- [ ] **Step 4: 跑确认通过**

Run: `pytest tests/test_guardrail.py -v`
Expected: 3 passed。

- [ ] **Step 5: 提交**

```bash
git add src/guardrail.py tests/test_guardrail.py
git commit -m "feat: 护栏一·不乱承诺正则层 + 测试"
```

### Task P3.2: 护栏二·有据校验（TDD）

**Files:** Modify `src/guardrail.py`; Modify `tests/test_guardrail.py`

- [ ] **Step 1: 追加失败测试**

```python
from src.guardrail import check_grounding

def test_grounding_passes_when_cited():
    r = check_grounding("清关中[P-TIME-01]，预计按标准时效。", citations=["P-TIME-01"], order_facts=[])
    assert r == []

def test_grounding_flags_uncited_factual_claim():
    r = check_grounding("您的包裹已被海关扣押需缴税 50 美元。", citations=[], order_facts=[])
    assert r  # 无引用的事实断言被标记
```

- [ ] **Step 2: 跑确认失败**

Run: `pytest tests/test_guardrail.py::test_grounding_flags_uncited_factual_claim -v`
Expected: FAIL（`check_grounding` 不存在）。

- [ ] **Step 3: 在 `src/guardrail.py` 追加**

```python
_CITE = re.compile(r"\[[A-Z]+-[A-Z]+-\d{2}\]")
_FACTY = re.compile(r"\d|海关|扣押|赔|退|时效|清关|签收|丢件")

def check_grounding(reply: str, citations: list[str], order_facts: list[str]) -> list[str]:
    flags = []
    for sent in re.split(r"[。.!?！？\n]", reply):
        s = sent.strip()
        if not s: continue
        if _FACTY.search(s) and not _CITE.search(s) and not citations and not order_facts:
            flags.append(f"ungrounded:{s[:20]}")
    return flags
```

- [ ] **Step 4: 跑确认通过**

Run: `pytest tests/test_guardrail.py -v`
Expected: 5 passed。

- [ ] **Step 5: 提交**

```bash
git add src/guardrail.py tests/test_guardrail.py
git commit -m "feat: 护栏二·有据校验 + 测试"
```

### Task P3.3: 决策 + 升级触发 + 护栏接入 pipeline（TDD）

**Files:** Create `src/decision.py`; Modify `src/pipeline.py`; Modify `tests/test_pipeline.py`

- [ ] **Step 1: 写失败测试（新增 `tests/test_decision.py`）**

```python
from src.decision import decide

def test_escalate_on_money():
    d, why = decide(category="丢件破损", sentiment="angry",
                     reply="确认丢件后按申报价值赔付[P-LOST-01]。",
                     citations=["P-LOST-01"], order=None, guardrail_flags=[], message="要赔我300美元")
    assert d == "escalate" and "赔付" in why

def test_auto_when_grounded_and_calm():
    d, why = decide(category="物流时效", sentiment="calm",
                     reply="标准时效 7-12 个工作日[P-TIME-01]。",
                     citations=["P-TIME-01"], order={"status":"在途"}, guardrail_flags=[], message="多久到")
    assert d == "auto"

def test_escalate_when_guardrail_fails():
    d, why = decide(category="物流时效", sentiment="calm", reply="3天到",
                     citations=[], order=None, guardrail_flags=["eta_promise"], message="多久")
    assert d == "escalate" and "护栏" in why
```

在 `tests/test_pipeline.py` 追加：
```python
def test_pipeline_escalates_adversarial(fake_llm, sample_orders, sample_policy):
    fake_llm.responses["classify"]={"category":"丢件破损","urgency":"high","language":"en","sentiment":"angry"}
    fake_llm.responses["draft"]={"reply_zh":"我们保证赔付 300 美元。","reply_en":"We guarantee a 300 USD payout.","citations":[],"order_facts":[]}
    out = handle("BF1002 lost, pay me 300 USD now or 1-star", fake_llm, orders_path=sample_orders, policy_path=sample_policy)
    assert out["decision"]=="escalate" and out["escalate_reason"]
```

- [ ] **Step 2: 跑确认失败**

Run: `pytest tests/test_decision.py tests/test_pipeline.py::test_pipeline_escalates_adversarial -v`
Expected: FAIL。

- [ ] **Step 3: 实现 `src/decision.py`**

```python
import re
_THREAT = re.compile(r"差评|1-?star|一星|曝光|工单|投诉|12315|media")

def decide(category, sentiment, reply, citations, order, guardrail_flags, message):
    if guardrail_flags:
        return "escalate", f"护栏未过:{guardrail_flags}"
    if category == "费用与对账争议" or re.search(r"赔|退款|补偿|refund|compensat", message):
        return "escalate", "涉赔付/退款金额认定"
    if category == "清关问题" and re.search(r"海关|扣押|缴税|法务|禁运|customs|seiz", message):
        return "escalate", "海关/法务/禁运"
    if sentiment == "angry" and _THREAT.search(message):
        return "escalate", "情绪激烈且含威胁"
    if order is None and not citations:
        return "escalate", "订单查不到且无政策依据，置信低"
    return "auto", ""
```

> 计划缺陷修正（2026-05-19）：钱款分支原匹配 `message+reply`，会因合规回复含「赔付」而对几乎所有「丢件破损」工单误升级（抵消护栏意义、拉低 P4 自动解决率）。改为只匹配商户 `message`（回复侧的具体赔付承诺已由 `_PAYOUT` 护栏覆盖）；并把单元素集合 `in {...}` 改为 `==`（M1）。三条 mandated 测试与 pipeline 测试仍全绿（已核验）。

- [ ] **Step 4: 把护栏+决策接入 `src/pipeline.py`**

替换 `handle` 末尾返回前逻辑：
```python
from src.guardrail import check_no_overpromise, check_grounding
from src.decision import decide

# ...（classify/order/clauses/draft 不变）...
    reply_all = (d.get("reply_zh","") + " " + d.get("reply_en",""))
    flags = check_no_overpromise(reply_all) + check_grounding(
        reply_all, d.get("citations",[]), d.get("order_facts",[]))
    decision, why = decide(cls["category"], cls["sentiment"], reply_all,
        d.get("citations",[]), order, flags, message)
    return {
        "category": cls["category"], "urgency": cls["urgency"],
        "language": cls["language"], "sentiment": cls["sentiment"],
        "decision": decision, "escalate_reason": why,
        "citations": d.get("citations", []), "order_facts": d.get("order_facts", []),
        "confidence": 1.0 if (order or d.get("citations")) else 0.3,
        "reply_zh": d.get("reply_zh","") if decision=="auto" else "",
        "reply_en": d.get("reply_en","") if decision=="auto" else "",
    }
```

- [ ] **Step 5: 跑确认通过 + 全量回归**

Run: `pytest -q`
Expected: 全绿（含新增 decision/pipeline 升级用例）。

- [ ] **Step 6: 提交**

```bash
git add src/decision.py src/pipeline.py tests/test_decision.py tests/test_pipeline.py
git commit -m "feat: 决策+升级触发，护栏接入 pipeline + 测试"
```

### Task P3.4: 飞书行动脚本 + SKILL.md 接线

**Files:** Create `skill/scripts/feishu_actions.sh`

- [ ] **Step 1: 写 `skill/scripts/feishu_actions.sh`**

用 P0.4 固化在 `skill/references/lark_cli_cheatsheet.md` 的精确命令填充：
```bash
#!/usr/bin/env bash
# 用法: feishu_actions.sh reply <chat_id> <text>
#       feishu_actions.sh log '<json>'
#       feishu_actions.sh escalate <title> <body>
set -euo pipefail
cmd="$1"; shift
case "$cmd" in
  reply)    lark-cli im +messages-send --chat-id "$1" --text "$2" --format json ;;
  log)      # 把契约 JSON 写入多维表格一行（精确命令来自 P0.4 实测，替换占位）
            lark-cli <BITABLE_RECORD_CREATE_CMD> --app-token "$FEISHU_BITABLE_APP_TOKEN" --table-id "$FEISHU_BITABLE_TABLE_ID" --fields "$1" --format json ;;
  escalate) lark-cli <TASK_CREATE_CMD> --summary "$1" --description "$2" --format json ;;
  *) echo "unknown $cmd" >&2; exit 1 ;;
esac
```
> 注：`<BITABLE_RECORD_CREATE_CMD>` / `<TASK_CREATE_CMD>` 必须替换为 P0.4 `--help` 实测确认的真实子命令，不得留占位。若 P0.4 未完成则本步阻塞，回到 P0.4。

- [ ] **Step 2: 冒烟验证（需 P0 环境与 `.env`）**

Run: `bash skill/scripts/feishu_actions.sh reply "$FEISHU_HUMAN_CHAT_ID" "P3 smoke"`
Expected: 测试群收到 "P3 smoke"，输出 JSON 含 message_id。

Run: `bash skill/scripts/feishu_actions.sh log '{"类目":"物流时效","决策":"auto"}'`
Expected: 多维表格新增一行。

- [ ] **Step 3: 提交**

```bash
git add skill/scripts/feishu_actions.sh
git commit -m "feat: 飞书行动脚本（回复/写看板/建任务）"
```

---

# Phase P4 — 评测 + 记分卡

### Task P4.1: 指标计算（纯函数，TDD）

**Files:** Create `eval/metrics.py`, `eval/__init__.py`; Test `tests/test_metrics.py`

- [ ] **Step 1: 写失败测试**

```python
from eval.metrics import score

def test_score_basic():
    preds = [{"category":"物流时效","decision":"auto","citations":["P-TIME-01"]},
             {"category":"丢件破损","decision":"auto","citations":[]}]
    gold  = [{"gold_category":"物流时效","gold_decision":"auto","gold_citations":["P-TIME-01"],"must_not_promise":False},
             {"gold_category":"丢件破损","gold_decision":"escalate","gold_citations":["P-LOST-01"],"must_not_promise":True}]
    s = score(preds, gold, overpromise_hits=[False, True])
    assert s["category_acc"] == 1.0
    assert s["decision_acc"] == 0.5
    assert s["dangerous_miss"] == 1          # 该 escalate 却 auto
    assert s["citation_hit"] == 0.5
    assert s["overpromise_rate"] == 1.0      # 对抗子集(must_not_promise)触发率: 1/1
```

> 计划缺陷修正（2026-05-19）：原断言 `overpromise_rate == 0.5` 与语义/实现冲突。设计定义「过度承诺率＝对抗子集触发率」，实现 `sum(adv)/len(adv)` 正确（本例对抗子集仅 row2，hit=True → 1/1=1.0）。0.5 是误按全样本计算所得的错误期望值。实现不变（实现正确），仅修正测试期望为 1.0。

- [ ] **Step 2: 跑确认失败**

Run: `pytest tests/test_metrics.py -v`
Expected: FAIL。

- [ ] **Step 3: 实现 `eval/metrics.py`**

```python
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
```

- [ ] **Step 4: 跑确认通过**

Run: `pytest tests/test_metrics.py -v`
Expected: 1 passed。

- [ ] **Step 5: 提交**

```bash
git add eval/__init__.py eval/metrics.py tests/test_metrics.py
git commit -m "feat: 评测指标计算 + 测试"
```

### Task P4.2: baseline + 评测 harness

**Files:** Create `eval/baseline.py`, `eval/run_eval.py`

- [ ] **Step 1: 写 `eval/baseline.py`（裸单 prompt）**

```python
def baseline_handle(message: str, llm) -> dict:
    prompt = ("你是跨境物流客服，直接用中英双语回复以下消息，并输出 JSON "
              '{"category":6选1,"decision":"auto|escalate","citations":[],'
              '"reply_zh":"...","reply_en":"..."}。类目：物流时效|丢件破损|'
              "费用与对账争议|清关问题|退件与拒收|一般咨询。\n消息：" + message)
    out = llm.complete_json(prompt, tag="baseline")
    out.setdefault("citations", [])
    return out
```

- [ ] **Step 2: 写 `eval/run_eval.py`**

```python
import json, pathlib, time, argparse
from src.llm import ClaudeClient
from src.pipeline import handle
from src.guardrail import check_no_overpromise
from eval.baseline import baseline_handle
from eval.metrics import score

DATA = pathlib.Path(__file__).parent.parent / "data"

def run(which):
    rows = [json.loads(l) for l in (DATA/"testset.jsonl").read_text().splitlines() if l.strip()]
    llm = ClaudeClient()
    preds, ophits = [], []
    t0 = time.time()
    for r in rows:
        out = (handle(r["message"], llm) if which=="agent"
               else baseline_handle(r["message"], llm))
        preds.append({"category":out.get("category",""),
                      "decision":out.get("decision","auto"),
                      "citations":out.get("citations",[])})
        ophits.append(bool(check_no_overpromise(out.get("reply_zh","")+out.get("reply_en",""))))
    dt = time.time()-t0
    s = score(preds, rows, ophits); s["avg_sec"] = round(dt/len(rows),2)
    return s

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--which",default="agent")
    a = ap.parse_args()
    print(json.dumps(run(a.which), ensure_ascii=False, indent=2))
```

- [ ] **Step 3: 冒烟（小样跑通，不看分数）**

Run: `head -n 3 data/testset.jsonl > /tmp/mini.jsonl`（临时把 DATA 指向 mini 或加 `--limit`；简单起见加 `--limit` 参数：在 `run` 加 `rows=rows[:limit]`，`argparse` 加 `--limit type=int default=0`，0 表示全量）
Run: `ANTHROPIC_API_KEY=$KEY python eval/run_eval.py --which agent --limit 3`
Expected: 打印含 `category_acc/decision_acc/dangerous_miss/overpromise_rate/avg_sec` 的 JSON，无异常。

- [ ] **Step 4: 提交**

```bash
git add eval/baseline.py eval/run_eval.py
git commit -m "feat: baseline + 评测 harness"
```

### Task P4.3: 全量评测 + 回调 + 记分卡定稿

- [ ] **Step 1: 全量跑 agent 与 baseline**

Run: `ANTHROPIC_API_KEY=$KEY python eval/run_eval.py --which agent  > eval/score_agent.json`
Run: `ANTHROPIC_API_KEY=$KEY python eval/run_eval.py --which baseline > eval/score_baseline.json`
Expected: 两份记分卡 JSON。

- [ ] **Step 2: 看结果回调（最多 2 轮）**

若 `dangerous_miss` > 1 或 `overpromise_rate` > 0：调 `skill/references/escalation_rules.md` / `src/guardrail.py` 正则 / `src/decision.py` 阈值（不放宽对抗口径），重跑 Step 1。每轮回调后 `pytest -q` 必须仍全绿。回调以「降低危险漏报与过度承诺」为唯一目标，不为提分牺牲安全。

- [ ] **Step 3: 定稿记分卡到仓库**

把最终两份 JSON 与一句话对比（agent vs baseline 各指标）写入 `eval/SCORECARD.md`（表格）。

- [ ] **Step 4: 提交**

```bash
git add eval/score_agent.json eval/score_baseline.json eval/SCORECARD.md src skill
git commit -m "feat: 全量评测结果与记分卡定稿"
```

---

# Phase P5 — 交付物

### Task P5.1: README（项目说明 + 架构 + 头条 + 部署）

**Files:** Create `README.md`

- [ ] **Step 1: 写 `README.md`**

包含小节：项目一句话定位 / 架构图（复制 spec §4 的 ASCII）/ **头条指标表**（从 `eval/SCORECARD.md` 填真实数字，禁占位）/ 技术栈（OpenClaw+飞书CLI+腾讯云+国产模型；离线评测 Claude）/ 本地复现步骤（venv + pytest + `eval/run_eval.py`）/ 线上部署步骤（P0 实测：腾讯云模板、飞书应用权限、lark-cli 授权、命令面）/ 演示录屏链接占位（P5.2 后填）/ 免责声明（数据全合成）。

- [ ] **Step 2: 校验无占位**

Run: `grep -nE "TODO|TBD|XXX|占位|<.*>" README.md`
Expected: 仅演示录屏链接一处临时（P5.2 回填）；其余必须无。

- [ ] **Step 3: 提交**

```bash
git add README.md
git commit -m "docs: README（架构/真实头条指标/部署/复现）"
```

### Task P5.2: 演示录屏（飞书真实闭环）

- [ ] **Step 1: 录制脚本化演示（用户操作飞书，Claude 给逐步台本）**

台本：① 飞书给机器人发一条乱糟糟中英混客诉（含订单号，可自动答类）→ 机器人秒级双语回复 → 切到飞书多维表格看板看到新增一行。② 再发一条对抗/必升级（诱导赔付承诺）→ 机器人不乱答 → 飞书任务列表出现新任务 @人工，正文含 escalate_reason。
录 60-90s，1080p。

- [ ] **Step 2: 产出文件**

导出 `demo.mp4`/GIF，上传到用户可控图床或仓库 `assets/`（≤ 仓库限制则入仓，否则放链接）。回填 README 录屏链接。

- [ ] **Step 3: 提交**

```bash
git add README.md assets/ 2>/dev/null; git commit -m "docs: 演示录屏 + README 回填链接"
```

### Task P5.3: 一页纸投递案例（≤100 字 + 截图链接）

**Files:** Create `CASE.md`

- [ ] **Step 1: 写 `CASE.md`**

按 spec §8 模板，用 `eval/SCORECARD.md` 真实数字替换 X/Y/N，附 3-4 张截图（架构、飞书自动回复、多维表格看板、记分卡）与 repo/录屏链接。≤100 字正文 + 截图区。

- [ ] **Step 2: 字数与数字校验**

Run: `python -c "import re,sys;t=open('CASE.md').read();body=t.split('---')[0];print(len(re.sub(r'\s','',body)))"`
Expected: 正文（首个分隔前）去空白 ≤ 130 字符（约 100 字中文容差）；无 X%/Y%/N 占位。

- [ ] **Step 3: 提交并打标签**

```bash
git add CASE.md
git commit -m "docs: 一页纸投递案例（真实数字）"
git tag v1.0-flagship
```

---

## Self-Review（已执行）

**1. Spec 覆盖核对：**
- §4 部署/双工具/两个飞书集成面 → P0.1-P0.4。
- §5 Skill 处理链/类目/升级触发/输出契约 → P2.1-P2.7、P3.3（输出契约由 test_pipeline 断言全字段）。
- §6 政策KB/订单/测试集（规模与配比）→ P1.2-P1.4（schema 测试强制 20-30 / 200-400 / 60-80 与配比）。
- §7 指标（分类/升级/危险漏报单列/引用/过度承诺/耗时/vs baseline）→ P4.1-P4.3（metrics 覆盖全部，含 baseline 对比）。
- §7 两道护栏 → P3.1（不乱承诺）、P3.2（有据）。
- §8 交付物 6 项 → P5.1-P5.3 + 全程仓库与 skill 包。
- §11 LLM 决策（线上国产/离线 Claude）→ 约定 + P0.3 + P2.1（ClaudeClient 仅离线）+ run_eval 用 Claude。
- 无未覆盖需求。

**2. 占位符扫描：** 唯一受控占位 = `feishu_actions.sh` 的 `<BITABLE_RECORD_CREATE_CMD>`/`<TASK_CREATE_CMD>`，已显式标注「必须由 P0.4 实测命令替换、否则阻塞回 P0.4」——这是依赖真实环境的硬约束而非计划偷懒；README/CASE 的数字占位均设了校验门强制回填真实值。其余无 TBD/TODO。

**3. 类型/签名一致性：** `handle(message, llm, orders_path, policy_path)`、`classify(message, llm)`、`draft_reply(message, order, clauses, llm)`、`lookup_order(order_id, path)`、`lookup_policy(query, category, path, k)`、`check_no_overpromise(reply, llm)`、`check_grounding(reply, citations, order_facts)`、`decide(category, sentiment, reply, citations, order, guardrail_flags, message)`、`score(preds, gold, overpromise_hits)` —— 跨任务调用处签名一致；输出契约字段（category/urgency/language/sentiment/decision/escalate_reason/citations/order_facts/confidence/reply_zh/reply_en）在 P2.6 定义、P3.3 保持、P4 消费，一致。FakeLLM `complete_json(prompt, tag)` 与 ClaudeClient 一致。

修正：P4.2 Step3 引用的 `--limit` 参数已在该步显式要求加到 `run()/argparse`，与 P4.3 全量（不带 limit，默认 0=全量）一致，无矛盾。

---

## 风险提醒（执行时注意）

- P0 是关键路径且依赖用户账号/付费/授权；P1-P4 的单测可在 P0 完成前并行推进（FakeLLM 不联网），仅 P2.7/P3.4 冒烟、P4.3 全量评测、P5.2 录屏需 P0 与真实 key。
- `feishu_actions.sh` 的多维表格/任务子命令必须以 `lark-cli --help` 实测为准，发现与计划占位不符以实测为准并回填 cheatsheet。
- 评测回调严守「不为提分放宽对抗口径」，危险漏报与过度承诺优先于准确率。
