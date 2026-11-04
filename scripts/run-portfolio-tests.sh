#!/usr/bin/env bash
# Portfolio test entry: browser contracts, Node integration tests and the
# static-snapshot guard.
#
#   scripts/run-portfolio-tests.sh
set -uo pipefail
cd "$(dirname "$0")/.."

# Browser tests need a preview server; start one unless the caller provides one.
export STUDIO_BASE_URL="${STUDIO_BASE_URL:-http://127.0.0.1:3000}"
server_pid=""
if ! curl -fsS -o /dev/null "$STUDIO_BASE_URL/" 2>/dev/null; then
  node serve.js >/tmp/portfolio-tests-server.log 2>&1 &
  server_pid=$!
  for _ in $(seq 1 40); do
    curl -fsS -o /dev/null "$STUDIO_BASE_URL/" 2>/dev/null && break
    sleep 0.25
  done
fi
cleanup() { [ -n "$server_pid" ] && kill "$server_pid" 2>/dev/null; }
trap cleanup EXIT

status=0

echo "== 浏览器用例 =="
python3 -m unittest $(ls tests/*.py | tr '\n' ' ') || status=1

# Transcoding tests need FFmpeg (FFMPEG_PATH or ~/.cache/portfolio-media-tools).
media_tests=(
  tests/media-optimizer-integration.mjs
  tests/optimized-media-integration.mjs
  tests/image-optimization-integration.mjs
)
node_tests=(tests/*.mjs)

if [ -n "${FFMPEG_PATH:-}" ] || command -v ffmpeg >/dev/null 2>&1 || [ -x "$HOME/.cache/portfolio-media-tools/ffmpeg" ]; then
  media_available=1
else
  media_available=0
  echo "== 跳过转码测试（未找到 FFmpeg：设置 FFMPEG_PATH 或安装到 ~/.cache/portfolio-media-tools）=="
fi
if [ "$media_available" = "0" ]; then
  for skip in "${media_tests[@]}"; do
    node_tests=("${node_tests[@]/$skip}")
  done
fi

echo "== Node 集成测试 =="
node --test "${node_tests[@]}" || status=1

echo "== 静态快照一致性 =="
node scripts/sync-work-catalogue.mjs --check || status=1

exit "$status"
