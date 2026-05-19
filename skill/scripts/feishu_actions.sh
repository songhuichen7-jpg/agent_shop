#!/usr/bin/env bash
# feishu_actions.sh — 飞书行动：回复 / 写看板 / 建任务
# Usage:
#   feishu_actions.sh reply <chat_id> <text>
#   feishu_actions.sh log <contract_json>
#   feishu_actions.sh escalate <title> <body>
# Env vars required: FEISHU_HUMAN_CHAT_ID, FEISHU_BITABLE_APP_TOKEN, FEISHU_BITABLE_TABLE_ID
set -euo pipefail

CMD="${1:-}"

case "$CMD" in

  reply)
    # feishu_actions.sh reply <chat_id> <text>
    CHAT_ID="${2:?reply requires chat_id as \$2}"
    TEXT="${3:?reply requires text as \$3}"
    lark-cli im +messages-send \
      --as bot \
      --chat-id "$CHAT_ID" \
      --text "$TEXT"
    ;;

  log)
    # feishu_actions.sh log <contract_json>
    CONTRACT_JSON="${2:?log requires contract_json as \$2}"

    # Build the bitable payload safely via python3 (avoids shell JSON injection)
    PAYLOAD=$(python3 -c "
import json, sys
data = json.loads(sys.argv[1])
category       = str(data.get('category', ''))
decision       = str(data.get('decision', ''))
escalate_reason = str(data.get('escalate_reason', '') or '')
citations      = data.get('citations', [])
if escalate_reason:
    note = escalate_reason
elif citations:
    note = str(citations[0])
else:
    note = 'auto'
payload = {'fields': ['类目', '决策', '升级原因'], 'rows': [[category, decision, note]]}
print(json.dumps(payload, ensure_ascii=False))
" "$CONTRACT_JSON")

    lark-cli base +record-batch-create \
      --as user \
      --base-token "${FEISHU_BITABLE_APP_TOKEN:?FEISHU_BITABLE_APP_TOKEN not set}" \
      --table-id  "${FEISHU_BITABLE_TABLE_ID:?FEISHU_BITABLE_TABLE_ID not set}" \
      --json "$PAYLOAD"
    ;;

  escalate)
    # feishu_actions.sh escalate <title> <body>
    TITLE="${2:?escalate requires title as \$2}"
    BODY="${3:?escalate requires body as \$3}"
    lark-cli task +create \
      --as user \
      --summary "$TITLE" \
      --description "$BODY" \
      --format json
    ;;

  *)
    echo "Unknown command: '$CMD'" >&2
    echo "Usage: feishu_actions.sh reply|log|escalate ..." >&2
    exit 1
    ;;

esac
