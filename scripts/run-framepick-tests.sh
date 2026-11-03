#!/bin/sh
# Run every Framepick test in one go.
#
#   scripts/run-framepick-tests.sh            combined repo, expects `node serve.js` on :3000
#   scripts/run-framepick-tests.sh --standalone
#       starts serve-framepick.js on :3100 and runs the same suite against the
#       post-split layout (site at / instead of /reel/), then stops the server.
#
# Override with PORT, STUDIO_BASE_URL, FRAMEPICK_BASE_PATH, FRAMEPICK_SITE_ROOT.
set -e
cd "$(dirname "$0")/.."

STANDALONE=0
[ "$1" = "--standalone" ] && STANDALONE=1

if [ "$STANDALONE" = "1" ]; then
  PORT="${PORT:-3100}"
  FRAMEPICK_BASE_PATH="${FRAMEPICK_BASE_PATH:-/}"
  FRAMEPICK_SITE_ROOT="${FRAMEPICK_SITE_ROOT:-$PWD/reel}"
  export FRAMEPICK_BASE_PATH FRAMEPICK_SITE_ROOT
  export STUDIO_BASE_URL="${STUDIO_BASE_URL:-http://127.0.0.1:$PORT}"
  node serve-framepick.js & SERVER=$!
  trap 'kill $SERVER 2>/dev/null || true' EXIT
  for _ in $(seq 1 100); do
    curl -sf -o /dev/null "$STUDIO_BASE_URL$FRAMEPICK_BASE_PATH" && break
    sleep 0.1
  done
  echo "Framepick standalone preview: $STUDIO_BASE_URL$FRAMEPICK_BASE_PATH"
else
  export STUDIO_BASE_URL="${STUDIO_BASE_URL:-http://127.0.0.1:3000}"
  export FRAMEPICK_BASE_PATH="${FRAMEPICK_BASE_PATH:-/reel/}"
  export FRAMEPICK_SITE_ROOT="${FRAMEPICK_SITE_ROOT:-$PWD/reel}"
  echo "Framepick combined preview: $STUDIO_BASE_URL$FRAMEPICK_BASE_PATH"
fi

python3 -m unittest \
  tests/framepick-library-smoke.py \
  tests/framepick-rankings-smoke.py \
  tests/framepick-reviews-smoke.py \
  tests/framepick-accounts-smoke.py \
  tests/framepick-demo-smoke.py \
  tests/framepick-discovery-scan-test.py

node --test tests/framepick-reviews-api-integration.mjs
node --test tests/framepick-library-store-integration.mjs
node --test tests/framepick-accounts-integration.mjs
node --test tests/framepick-orders-integration.mjs
node --test tests/framepick-discovery-integration.mjs
node --test tests/framepick-publish-rules-test.mjs
node --test tests/framepick-creators-integration.mjs
node --test tests/framepick-creators-store-integration.mjs

# Publish-time guards: card fields, and the page matching the catalogue store.
node scripts/check-framepick-library.mjs --site "$FRAMEPICK_SITE_ROOT"
if [ -f "$HOME/.framepick/library/library.json" ]; then
  node scripts/build-framepick-library.mjs --site "$FRAMEPICK_SITE_ROOT" --check
else
  echo "跳过片库一致性检查：还没有作品表（先跑 scripts/framepick-library-cli.mjs seed）"
fi
