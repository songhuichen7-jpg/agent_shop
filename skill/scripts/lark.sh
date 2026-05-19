#!/usr/bin/env bash
# 统一 lark-cli 入口：固定已授权配置(HOME 持久卷) + 二进制绝对路径。
# 服务器容器内：配置/凭据在 /home/node/runtime/larkhome（挂载卷，重建不丢）。
exec env HOME="${LARK_HOME_DIR:-/home/node/runtime/larkhome}" \
  /home/node/runtime/npm/node_modules/.bin/lark-cli "$@"
