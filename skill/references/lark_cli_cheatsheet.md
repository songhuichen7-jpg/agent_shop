# lark-cli 命令面备忘（P0.4 实测后填入）

> 本机已核对 `lark-cli version 1.0.32`：多维表格命令叫 `base`，不是旧资料里的 `bitable`。
> 下面是可执行模板，真实 `chat_id` / `base-token` / `table-id` / 人员 ID 只放 `.env`，不要提交。

## 发消息

```bash
lark-cli im +messages-send \
  --as bot \
  --chat-id "$FEISHU_HUMAN_CHAT_ID" \
  --text "P0 smoke" \
  --format json
```

如果机器人不在群里或无发送权限，先把自建应用机器人拉进测试群，并确认 IM 权限与应用版本已发布。

## 多维表格新增记录

```bash
lark-cli base +record-batch-create \
  --as user \
  --base-token "$FEISHU_BITABLE_APP_TOKEN" \
  --table-id "$FEISHU_BITABLE_TABLE_ID" \
  --json '{"fields":["类目","决策","备注"],"rows":[["smoke","auto","P0 smoke"]]}'
```

写入前先确认表里有这些字段；字段名必须和飞书多维表格完全一致。

## 建任务

```bash
lark-cli task +create \
  --as user \
  --summary "P0 smoke task" \
  --description "由 agent_shop P0 冒烟测试创建" \
  --format json
```

如果要派给人工，可追加 `--assignee "<open_id>"`；人工 ID 不提交，按需放 `.env` 或现场传参。

## 鉴权检查

```bash
lark-cli doctor
lark-cli auth check --scope "im:message bitable:app task:task"
```

`auth check` 在当前版本必须传 `--scope`，裸跑会报 `required flag(s) "scope" not set`。
