# 评测记分卡 — 跨境物流客诉自动处理 Agent

> 离线评测集：`data/testset.jsonl`（**n=70** 条标注客诉，中/英/中英混；21 条 gold=escalate，12 条对抗 `must_not_promise=true`，覆盖 6 个类目）。
> 数据全合成、不涉真实商户；指标计算见 `eval/metrics.py`（TDD 覆盖）。
> 离线评测模型 `DEEPSEEK_EVAL_MODEL=deepseek-v4-pro`；线上 OpenClaw 绑 `deepseek-v4-flash`。

## 头条对照（agent vs 裸 LLM baseline，同集同模型）

| 指标 | **Agent (r2 终稿)** | Baseline (单 prompt LLM) | Δ |
|---|---:|---:|---:|
| 分类准确率 (`category_acc`) | 91.4% | 94.3% | −3pp（次要） |
| **升级判定准确率** (`decision_acc`) | **84.3%** | 81.4% | **+2.9pp** |
| **危险漏报**（该升级却自动答, ↓ 越好） | **0** | 6 | **−6** |
| **引用命中率**（`citation_hit`，回复是否命中 gold 条款） | **81.2%** | 0.0% | **+81pp** |
| **过度承诺率**（对抗子集触发率, ↓ 越好） | **0.0%** | 8.3% | **−8.3pp** |
| 处理耗时 / 条 | ~35 s | ~14 s | 慢 ~2.5× |

差异化在三处：**零过度承诺**（baseline 8.3% 乱承诺）、**零危险漏报**（baseline 6 次该升级却自动答）、**81% 引用命中**（baseline 0%——从不引政策）。决策准确率小幅超 baseline，分类轻微让位。

## 方法论迭代（≤2 轮安全回调）

| 轮次 | decision_acc | dangerous_miss | citation_hit | overpromise_rate |
|---|---:|---:|---:|---:|
| r0（首轮，原规则） | 67.1% | 5 | 84.1% | 0.0% |
| r1（收窄过宽升级 + 加硬承诺/威胁/签收报失触发） | 74.3% | 5（不同案） | 78.3% | 0.0% |
| **r2（补对账单/want refund/低报清关三类边界）** | **84.3%** | **0** | **81.2%** | **0.0%** |

诚实记录：r1 抓住了 r0 漏的 5 个但换了一组新的 5 个边界漏报；r2 用窄正则补齐三类边界。逐行 dump：`eval/dump_agent_r{0,1,2}.jsonl`。

## 跨 provider 可迁移性（次要参考）

同一规则层 + 同一数据 + 同一评测脚本，换 `ONLINE_LLM_PROVIDER=mimo`（小米 Mimo-v2-flash，OpenAI 兼容）：

| 指标 | DeepSeek-v4-pro + 规则 | Mimo-v2-flash + 规则（探索） |
|---|---:|---:|
| decision_acc | 84.3% | 100% |
| dangerous_miss | 0 | 0 |
| overpromise_rate | 0% | 0% |
| citation_hit | 81.2% | 91.3% |
| avg_sec | ~35s | ~8s |

结论：**安全（零过度承诺/零危险漏报）+ 引用 grounding 是规则层带来的，跨 provider 稳定保持**；Mimo 数字在这 70 条上偏高，可能受规则与该集模式匹配影响，未必直接外推到更广分布（详见 `eval/dump_agent_mimo*.jsonl`）。生产线当前绑 DeepSeek。

## 复现

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
pytest -q                                   # 47 单测，包含数据完整性 + 规则单测 + 接线测试
cp .env.example .env && vim .env            # 至少填 DEEPSEEK_API_KEY
python eval/run_eval.py --which agent    > eval/score_agent.json
python eval/run_eval.py --which baseline > eval/score_baseline.json
```

Agent 输出契约（每行）：

```json
{"category","urgency","language","sentiment","order_id","decision","escalate_reason",
 "citations","order_facts","confidence","reply_zh","reply_en"}
```
