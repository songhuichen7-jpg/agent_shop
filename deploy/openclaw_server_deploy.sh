#!/usr/bin/env bash
# 跨境客诉助手 — OpenClaw 服务器侧部署脚本（幂等、分阶段、带日志）
#
# 只操作 ~/openclaw-agent-shop 栈；绝不触碰 youshi-* 容器/卷/数据。
# 在腾讯云服务器上以 ubuntu 用户运行：
#   bash openclaw_server_deploy.sh prep      # 备份 + 幂等加挂载卷 + mkdir runtime
#   bash openclaw_server_deploy.sh recreate  # 仅重建 gateway，校验 youshi 未变
#   bash openclaw_server_deploy.sh deps      # 容器内装 openai(venv) + lark-cli(npm)
#   bash openclaw_server_deploy.sh discover  # 只读：导出 OpenClaw skill 注册机制
#   bash openclaw_server_deploy.sh rollback  # 还原 compose+openclaw.json 备份并重建
#
# 每步日志写入 ~/openclaw-agent-shop/deploy.log，同时打印 STAGE 标记。

set -uo pipefail
STACK_DIR="$HOME/openclaw-agent-shop"
APP_DIR="$STACK_DIR/agent_shop"
LOG="$STACK_DIR/deploy.log"
GW="openclaw-agent-shop-gateway"
TS="$(date +%Y%m%d%H%M%S)"
D(){ command -v docker >/dev/null && (docker "$@" 2>/dev/null || sudo -n docker "$@"); }

log(){ echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"; }
stage(){ echo "==== STAGE $* ($(date +%H:%M:%S)) ====" | tee -a "$LOG"; }

cd "$STACK_DIR" || { echo "no $STACK_DIR"; exit 2; }

case "${1:-}" in
prep)
  stage prep
  cp "docker-compose.yml" "docker-compose.yml.bak.$TS" && log "compose backed up .bak.$TS"
  [ -f state/openclaw.json ] && cp state/openclaw.json "state/openclaw.json.bak.$TS" && log "openclaw.json backed up .bak.$TS"
  if grep -q "/home/node/agent_shop" docker-compose.yml; then
    log "volumes already patched, skip"
  else
    python3 - <<'PY'
import pathlib
p=pathlib.Path("docker-compose.yml"); lines=p.read_text().splitlines(); out=[]
for ln in lines:
    out.append(ln)
    if ln.strip()=="- ./state:/home/node/.openclaw":
        out.append("      - ./agent_shop:/home/node/agent_shop:ro")
        out.append("      - ./runtime:/home/node/runtime")
p.write_text("\n".join(out)+"\n")
print("compose patched")
PY
    log "compose patched with agent_shop(ro)+runtime volumes"
  fi
  mkdir -p runtime && log "runtime/ ready"
  echo "--- volumes block ---"; sed -n '/volumes:/,/^[a-z]/p' docker-compose.yml | sed '/^[a-z]/d' | tee -a "$LOG"
  log "prep DONE"
  ;;

recreate)
  stage recreate
  log "youshi BEFORE:"; D ps --format '{{.Names}} {{.Status}}' | grep youshi | tee -a "$LOG"
  log "recreating gateway (compose project = openclaw-agent-shop only)"
  D compose up -d 2>&1 | tail -3 | tee -a "$LOG"
  sleep 7
  log "gateway AFTER:"; D ps --format '{{.Names}} {{.Status}}' | grep "$GW" | tee -a "$LOG"
  log "youshi AFTER (must be same uptime as before):"; D ps --format '{{.Names}} {{.Status}}' | grep youshi | tee -a "$LOG"
  log "container mounts:"; D exec "$GW" sh -lc 'ls -ld /home/node/agent_shop /home/node/runtime && ls /home/node/agent_shop/skill && python3 -V' 2>&1 | tee -a "$LOG"
  log "recreate DONE"
  ;;

deps)
  stage deps
  D exec -u node "$GW" sh -lc '
    set -e
    python3 -m venv /home/node/runtime/venv 2>/dev/null || true
    /home/node/runtime/venv/bin/pip -q install -i https://pypi.tuna.tsinghua.edu.cn/simple openai 2>/dev/null \
      || /home/node/runtime/venv/bin/pip -q install openai
    echo "openai: $(/home/node/runtime/venv/bin/python -c "import openai;print(openai.__version__)")"
    mkdir -p /home/node/runtime/npm
    npm i --prefix /home/node/runtime/npm --registry=https://registry.npmmirror.com @larksuite/cli >/dev/null 2>&1 \
      || npm i --prefix /home/node/runtime/npm @larksuite/cli >/dev/null 2>&1
    echo "lark-cli: $(/home/node/runtime/npm/node_modules/.bin/lark-cli --version 2>/dev/null || echo INSTALL_FAILED)"
  ' 2>&1 | tee -a "$LOG"
  log "deps DONE (openai in venv, lark-cli in /home/node/runtime/npm)"
  ;;

discover)
  stage discover
  log "OpenClaw skills list/check + config (read-only, for registration-path decision):"
  D exec "$GW" sh -lc 'node openclaw.mjs skills list 2>&1 | head -40; echo "--- skills check ---"; node openclaw.mjs skills check 2>&1 | head -20' 2>&1 | tee -a "$LOG"
  D exec "$GW" sh -lc 'echo "--- openclaw.json skills section ---"; python3 -c "import json;d=json.load(open(\"/home/node/.openclaw/openclaw.json\"));print(json.dumps(d.get(\"skills\",{}),ensure_ascii=False,indent=1)[:1500])"' 2>&1 | tee -a "$LOG"
  D exec "$GW" sh -lc 'echo "--- workspace/agents/plugin-skills tree ---"; find /home/node/.openclaw/workspace /home/node/.openclaw/agents /home/node/.openclaw/plugin-skills -maxdepth 3 2>/dev/null | head -40' 2>&1 | tee -a "$LOG"
  log "discover DONE — inspect deploy.log to decide skill registration path"
  ;;

rollback)
  stage rollback
  cb=$(ls -1t docker-compose.yml.bak.* 2>/dev/null | head -1)
  ob=$(ls -1t state/openclaw.json.bak.* 2>/dev/null | head -1)
  [ -n "$cb" ] && cp "$cb" docker-compose.yml && log "compose restored from $cb"
  [ -n "$ob" ] && cp "$ob" state/openclaw.json && log "openclaw.json restored from $ob"
  D compose up -d 2>&1 | tail -3 | tee -a "$LOG"
  sleep 6
  D ps --format '{{.Names}} {{.Status}}' | grep -E "$GW|youshi" | tee -a "$LOG"
  log "rollback DONE"
  ;;

*)
  echo "usage: $0 {prep|recreate|deps|discover|rollback}"; exit 1;;
esac
