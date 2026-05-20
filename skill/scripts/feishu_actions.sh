#!/usr/bin/env bash
# feishu_actions.sh — 飞书行动：回复 / 写看板 / 建任务
# Usage:
#   feishu_actions.sh reply <chat_id> <text>
#   feishu_actions.sh log <contract_json>
#   feishu_actions.sh escalate <title> <body>
# Env vars required: FEISHU_HUMAN_CHAT_ID, FEISHU_BITABLE_APP_TOKEN, FEISHU_BITABLE_TABLE_ID
set -euo pipefail

# 统一经 lark.sh 包装（固定已授权配置 HOME + "$LARK" 路径）
LARK="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lark.sh"

CMD="${1:-}"

case "$CMD" in

  reply)
    # feishu_actions.sh reply <chat_id> <text>
    CHAT_ID="${2:?reply requires chat_id as \$2}"
    TEXT="${3:?reply requires text as \$3}"
    "$LARK" im +messages-send \
      --as bot \
      --chat-id "$CHAT_ID" \
      --text "$TEXT"
    ;;

  log)
    # feishu_actions.sh log <contract_json>
    CONTRACT_JSON="${2:?log requires contract_json as \$2}"

    # Build the bitable payload safely via python3 (avoids shell JSON injection)
    PAYLOAD=$(python3 -c "
import datetime, json, os, sys
data = json.loads(sys.argv[1])

def text(key):
    value = data.get(key)
    return '' if value is None else str(value)

def joined(key):
    value = data.get(key, [])
    if isinstance(value, list):
        return ','.join(str(item) for item in value)
    return '' if value is None else str(value)

decision = text('decision')
urgency = text('urgency')
urgency = {'normal': 'medium', 'medium': 'medium', 'low': 'low', 'high': 'high'}.get(urgency, urgency or 'medium')
status = '已升级人工' if decision == 'escalate' else '已自动回复'
created_at = text('created_at') or datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
message_id = text('message_id') or os.environ.get('FEISHU_MESSAGE_ID', '')
escalate_reason = text('escalate_reason') or None

fields = [
    '原始消息', '类目', '决策', '中文回复', '英文回复', '引用条款',
    '订单号', '消息ID', '创建时间', '紧急度', '处理状态', '升级原因',
]
row = [
    text('message'), text('category'), decision, text('reply_zh'), text('reply_en'),
    joined('citations'), text('order_id'), message_id or None, created_at,
    urgency, status, escalate_reason,
]
payload = {'fields': fields, 'rows': [row]}
print(json.dumps(payload, ensure_ascii=False))
" "$CONTRACT_JSON")

    "$LARK" base +record-batch-create \
      --as user \
      --base-token "${FEISHU_BITABLE_APP_TOKEN:?FEISHU_BITABLE_APP_TOKEN not set}" \
      --table-id  "${FEISHU_BITABLE_TABLE_ID:?FEISHU_BITABLE_TABLE_ID not set}" \
      --json "$PAYLOAD"
    ;;

  escalate)
    # feishu_actions.sh escalate <title> <body>
    TITLE="${2:?escalate requires title as \$2}"
    BODY="${3:?escalate requires body as \$3}"
    EXTRA_ARGS=()
    ASSIGNEE="${FEISHU_TASK_ASSIGNEE_ID:-${FEISHU_HUMAN_OPEN_ID:-}}"
    if [[ -z "$ASSIGNEE" ]]; then
      ASSIGNEE=$("$LARK" auth status 2>/dev/null | python3 -c "
import json, sys
try:
    print(json.load(sys.stdin).get('userOpenId', ''))
except Exception:
    print('')
")
    fi
    if [[ -n "$ASSIGNEE" ]]; then
      EXTRA_ARGS+=(--assignee "$ASSIGNEE")
    fi
    if [[ -n "${FEISHU_MESSAGE_ID:-}" ]]; then
      EXTRA_ARGS+=(--idempotency-key "$FEISHU_MESSAGE_ID")
    fi
    "$LARK" task +create \
      --as user \
      --summary "$TITLE" \
      --description "$BODY" \
      --format json \
      "${EXTRA_ARGS[@]}"
    ;;

  *)
    echo "Unknown command: '$CMD'" >&2
    echo "Usage: feishu_actions.sh reply|log|escalate ..." >&2
    exit 1
    ;;

esac
