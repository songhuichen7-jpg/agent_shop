#!/usr/bin/env bash
# 把 跨境客诉助手 操作指令幂等接入 OpenClaw agent 工作区（AGENTS.md / TOOLS.md）。
# 工作区是 git 仓 → 改动可 revert。只动 openclaw-agent-shop 的 workspace，不碰 youshi。
# 用法（服务器 ubuntu）: bash wire_agents_md.sh apply | restart | rollback
set -uo pipefail
GW="openclaw-agent-shop-gateway"
WS="/home/node/.openclaw/workspace"
SECT_A="/home/node/agent_shop/deploy/AGENTS_kuajing_section.md"
SECT_T="/home/node/agent_shop/deploy/TOOLS_kuajing_section.md"
MARK="跨境客诉助手 (agent_shop) — 飞书客诉自动处理"
DX(){ sudo -n docker exec -u node "$GW" sh -lc "$1"; }
log(){ echo "[$(date +%H:%M:%S)] $*"; }

case "${1:-}" in
apply)
  log "workspace git backup commit (restore point)"
  DX "cd $WS && (git add -A && git -c user.email=a@a -c user.name=deploy commit -q -m 'backup before agent_shop wiring '\$(date +%Y%m%d%H%M%S) || echo 'nothing to backup / already clean') && git log --oneline -1"
  if DX "grep -q '$MARK' $WS/AGENTS.md"; then
    log "AGENTS.md already wired, skip append"
  else
    log "append AGENTS.md + TOOLS.md sections"
    DX "cat $SECT_A >> $WS/AGENTS.md && cat $SECT_T >> $WS/TOOLS.md && echo appended"
    DX "cd $WS && git add -A && git -c user.email=a@a -c user.name=deploy commit -q -m 'feat: 接入 跨境客诉助手 操作流程 (AGENTS.md/TOOLS.md)' && git log --oneline -2"
  fi
  log "tail AGENTS.md"; DX "tail -8 $WS/AGENTS.md"
  ;;
restart)
  log "restart gateway so workspace startup context reloads (youshi untouched)"
  cd ~/openclaw-agent-shop && (sudo -n docker compose up -d 2>&1 | tail -2)
  sleep 7
  (sudo -n docker ps --format '{{.Names}} {{.Status}}' | grep -E "$GW|youshi")
  ;;
rollback)
  log "revert workspace to backup commit"
  DX "cd $WS && git log --oneline -4 && git reset --hard HEAD~1 && git log --oneline -1"
  log "rollback DONE (restart gateway separately if needed)"
  ;;
*) echo "usage: $0 {apply|restart|rollback}"; exit 1;;
esac
