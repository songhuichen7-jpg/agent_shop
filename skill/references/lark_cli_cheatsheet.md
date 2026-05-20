# lark-cli 命令面备忘（P0.4 实测后填入）

> 本机已核对 `lark-cli version 1.0.32`：多维表格命令叫 `base`，不是旧资料里的 `bitable`。
> 下面是可执行模板，真实 `chat_id` / `base-token` / `table-id` / 人员 ID 只放 `.env`，不要提交。

## 发消息

```bash
lark-cli im +messages-send \
  --as bot \
  --chat-id "$FEISHU_HUMAN_CHAT_ID" \
  --text "P0 smoke"
```

如果机器人不在群里或无发送权限，先把自建应用机器人拉进测试群，并确认 IM 权限与应用版本已发布。

## 多维表格新增记录

```bash
lark-cli base +record-batch-create \
  --as user \
  --base-token "$FEISHU_BITABLE_APP_TOKEN" \
  --table-id "$FEISHU_BITABLE_TABLE_ID" \
  --json '{"fields":["原始消息","类目","决策","中文回复","英文回复","引用条款","订单号","消息ID","创建时间","紧急度","处理状态","升级原因"],"rows":[["BF1001 delayed","物流时效","auto","中文回复","English reply","P-TIME-01","BF1001",null,"2026-05-20 10:00:00","medium","已自动回复",null]]}'
```

写入前先确认表里有这些字段；字段名必须和飞书多维表格完全一致。

## 建任务

```bash
lark-cli task +create \
  --as user \
  --summary "P0 smoke task" \
  --description "由 agent_shop P0 冒烟测试创建" \
  --assignee "$FEISHU_TASK_ASSIGNEE_ID" \
  --format json
```

如果要派给人工，可追加 `--assignee "<open_id>"`；人工 ID 不提交，按需放 `.env` 或现场传参。

## 鉴权检查

```bash
lark-cli doctor
lark-cli auth check --scope "im:message bitable:app task:task:write"
```

`auth check` 在当前版本必须传 `--scope`，裸跑会报 `required flag(s) "scope" not set`。

> 修正(2026-05-20, P3.4 实测)：im +messages-send 无 --format json；多维表格文本列名为「升级原因」非「备注」。
> 修正(2026-05-20)：看板写入覆盖 12 列；`urgency=normal` 写入飞书前映射为「medium」，避免自动新增单选项。
