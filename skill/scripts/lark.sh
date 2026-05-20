#!/usr/bin/env bash
# 统一 lark-cli 入口：服务器优先使用持久卷配置；本地开发回退到 PATH。
SERVER_LARK="/home/node/runtime/npm/node_modules/.bin/lark-cli"

if [[ -n "${LARK_CLI_BIN:-}" ]]; then
  LARK_BIN="$LARK_CLI_BIN"
elif [[ -x "$SERVER_LARK" ]]; then
  LARK_BIN="$SERVER_LARK"
else
  LARK_BIN="$(command -v lark-cli || true)"
fi

if [[ -z "$LARK_BIN" || ! -x "$LARK_BIN" ]]; then
  echo "lark-cli not found; set LARK_CLI_BIN or install lark-cli" >&2
  exit 127
fi

if [[ -n "${LARK_HOME_DIR:-}" ]]; then
  exec env HOME="$LARK_HOME_DIR" "$LARK_BIN" "$@"
elif [[ -d /home/node/runtime/larkhome ]]; then
  exec env HOME="/home/node/runtime/larkhome" "$LARK_BIN" "$@"
else
  exec "$LARK_BIN" "$@"
fi
