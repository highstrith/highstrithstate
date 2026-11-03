#!/bin/bash
# 帧选「一条命令上线」：取封面 → 转图 → 上传 OSS → 重建页面 → 校验 → 部署 → 线上复核。
#
#   scripts/framepick-ship.sh "第三批 5 部上架"           全流程（含浏览器测试）
#   scripts/framepick-ship.sh "第三批 5 部上架" --fast    跳过浏览器测试，只跑校验
#   scripts/framepick-ship.sh "..." --no-push             只做到本地校验，不部署
#   scripts/framepick-ship.sh "..." --with-douyin         先用登录态浏览器刷新抖音封面
#
# 一次性准备（只做一次）：
#   1. ~/bin/ossutil config   写入 ~/.ossutilconfig（endpoint oss-cn-hangzhou.aliyuncs.com）
#   2. ego-browser 保持登录抖音，仅 --with-douyin 时需要
set -uo pipefail
cd "$(dirname "$0")/.." || exit 2

MSG="${1:-}"
if [ -z "$MSG" ]; then
  echo "用法：scripts/framepick-ship.sh \"提交说明\" [--fast] [--no-push] [--with-douyin]" >&2
  exit 2
fi
shift

FAST=0; PUSH=1; WITH_DOUYIN=0
for flag in "$@"; do
  case "$flag" in
    --fast) FAST=1 ;;
    --no-push) PUSH=0 ;;
    --with-douyin) WITH_DOUYIN=1 ;;
    *) echo "未知参数：$flag" >&2; exit 2 ;;
  esac
done

step() { printf '\n\033[1m▸ %s\033[0m\n' "$1"; }
fail() { printf '\033[31m✗ %s\033[0m\n' "$1" >&2; exit 1; }

step "0/7 检查环境"
command -v node >/dev/null || fail "找不到 node"
if [ "$PUSH" = "1" ] && [ ! -f "$HOME/.ossutilconfig" ]; then
  fail "还没配 ossutil 凭据：先跑 ~/bin/ossutil config（endpoint: oss-cn-hangzhou.aliyuncs.com）"
fi
echo "  工作目录 $(pwd)"

if [ "$WITH_DOUYIN" = "1" ]; then
  step "1/7 刷新抖音封面（登录态浏览器）"
  if ego-browser nodejs < scripts/framepick-cover-douyin.js; then
    echo "  抖音封面已刷新"
  else
    echo "  ! 抖音封面抓取失败（多半是没登录），沿用已有封面继续"
  fi
else
  step "1/7 刷新抖音封面 — 跳过（需要时加 --with-douyin）"
fi

step "2/7 取封面并转 640w webp"
node scripts/framepick-cover-build.mjs || fail "封面构建失败，见上面的 ✗ 行"

if [ "$PUSH" = "1" ]; then
  step "3/7 上传封面到 OSS"
  find reel/img -name '._*' -type f -delete 2>/dev/null
  "$HOME/bin/ossutil" cp -r --update --jobs 4 \
    --include "*.webp" --exclude "._*" \
    --meta "Cache-Control:public,max-age=600" \
    reel/img/ oss://highstrith-assets/reel/img/ 2>&1 | tail -3 || fail "上传失败"
  step "3b/7 线上封面自检"
  BAD=0
  for file in reel/img/*.webp; do
    name=$(basename "$file")
    code=$(curl -s -o /dev/null -w '%{http_code}' -I "https://highstrith-assets.oss-cn-hangzhou.aliyuncs.com/reel/img/$name")
    [ "$code" = "200" ] || { echo "  $code $name"; BAD=$((BAD+1)); }
  done
  [ "$BAD" -eq 0 ] && echo "  全部 200" || fail "有 $BAD 张封面在 OSS 上不可访问，先别部署"
else
  step "3/7 上传 OSS — 跳过（--no-push）"
fi

step "4/7 重建页面并校验"
node scripts/build-framepick-library.mjs || fail "页面重建失败"
node scripts/check-framepick-library.mjs || fail "卡片校验未通过"

if [ "$FAST" = "0" ]; then
  step "5/7 全量测试（约 2 分钟）"
  ./scripts/run-framepick-tests.sh --standalone > /tmp/framepick-ship-tests.log 2>&1
  if [ $? -eq 0 ]; then
    grep -E '^Ran |^OK' /tmp/framepick-ship-tests.log | tail -2
  else
    grep -E '^(FAIL|ERROR):' /tmp/framepick-ship-tests.log | head -10
    fail "测试未通过，日志在 /tmp/framepick-ship-tests.log"
  fi
else
  step "5/7 全量测试 — 跳过（--fast）"
fi

step "6/7 提交并部署"
DEPLOYED=0
if git diff --quiet && git diff --cached --quiet; then
  echo "  没有文件改动，跳过提交与部署"
else
  git add -A
  git commit -q -m "$MSG" || fail "提交失败"
  echo "  已提交 $(git log --oneline -1)"
  if [ "$PUSH" = "1" ]; then
    git push origin release/white-pages 2>&1 | tail -1 || fail "推送失败"
    git push origin HEAD:main 2>&1 | tail -1 || fail "推送 main 失败（没推 main 不会部署）"
    DEPLOYED=1
  fi
fi

if [ "$DEPLOYED" = "1" ]; then
  step "7/7 等部署并复核线上"
  for _ in $(seq 1 12); do
    sleep 20
    S=$(curl -s "https://api.github.com/repos/highstrith/highstrithstate/actions/runs?per_page=1" \
      | python3 -c "import json,sys; d=json.loads(sys.stdin.read(),strict=False)['workflow_runs'][0]; print(d['status'], d['conclusion'])" 2>/dev/null)
    echo "  $S"
    case "$S" in *success*|*failure*) break;; esac
  done
  case "$S" in
    *success*) ;;
    *) fail "部署未成功（状态：$S），到 Actions 页面看日志" ;;
  esac
  sleep 5
  curl -s "https://highstrith.github.io/highstrithstate/reel/?cb=$(date +%s)" -o /tmp/framepick-live.html
  python3 - <<'PY'
import re, subprocess
h = open('/tmp/framepick-live.html', encoding='utf-8').read()
cards = len(re.findall(r'<article class="card"', h))
srcs = sorted(set(re.findall(r'<img[^>]+src="([^"]+)"', h)))
bad = [s for s in srcs if subprocess.run(['curl','-s','-o','/dev/null','-w','%{http_code}','-I',s],
        capture_output=True, text=True).stdout.strip() != '200']
print(f'  线上：{cards} 张卡片 · {len(srcs)} 张封面 · 破图 {len(bad)} 张')
for s in bad: print('    ', s)
PY
else
  step "7/7 部署 — 跳过（--no-push）"
fi

printf '\n\033[32m完成\033[0m\n'
