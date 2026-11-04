#!/bin/bash
# 帧选「一条命令上线」：取封面 → 转图 → 上传 OSS → 重建页面 → 校验 → 部署两站 → 线上复核。
#
#   scripts/framepick-ship.sh "第三批 5 部上架"           全流程（含浏览器测试）
#   scripts/framepick-ship.sh "第三批 5 部上架" --fast    跳过浏览器测试，只跑校验
#   scripts/framepick-ship.sh "..." --no-push             只做到本地校验，不部署
#   scripts/framepick-ship.sh "..." --with-douyin         先用登录态浏览器刷新抖音封面
#
# 部署目标（2026-11-04 起两站分离）：
#   · 橘生梦厂 → 独立仓库 highstrith/jusheng（https://highstrith.github.io/jusheng/），
#     产物目录 /Volumes/E61--/网站/jusheng，由本脚本从 reel/ 同步
#   · 作品集   → 主仓库 highstrithstate 照旧推 release/white-pages + main
#   顺带同步本地预览副本 /Volumes/E61--/网站/framepick-live（serve-framepick.js 用）。
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

step "0/8 检查环境"
command -v node >/dev/null || fail "找不到 node"
if [ "$PUSH" = "1" ] && [ ! -f "$HOME/.ossutilconfig" ]; then
  fail "还没配 ossutil 凭据：先跑 ~/bin/ossutil config（endpoint: oss-cn-hangzhou.aliyuncs.com）"
fi
echo "  工作目录 $(pwd)"

if [ "$WITH_DOUYIN" = "1" ]; then
  step "1/8 刷新抖音封面（登录态浏览器）"
  if ego-browser nodejs < scripts/framepick-cover-douyin.js; then
    echo "  抖音封面已刷新"
  else
    echo "  ! 抖音封面抓取失败（多半是没登录），沿用已有封面继续"
  fi
else
  step "1/8 刷新抖音封面 — 跳过（需要时加 --with-douyin）"
fi

step "2/8 取封面并转 640w webp"
node scripts/framepick-cover-build.mjs || fail "封面构建失败，见上面的 ✗ 行"

if [ "$PUSH" = "1" ]; then
  step "3/8 上传封面到 OSS"
  find reel/img -name '._*' -type f -delete 2>/dev/null
  "$HOME/bin/ossutil" cp -r --update --jobs 4 \
    --include "*.webp" --exclude "._*" \
    --meta "Cache-Control:public,max-age=600" \
    reel/img/ oss://highstrith-assets/reel/img/ 2>&1 | tail -3 || fail "上传失败"
  # 作品集首页三张推荐卡封面走 assets/film-recommendation/，不再依赖 reel/img
  find assets/film-recommendation -name '._*' -type f -delete 2>/dev/null
  "$HOME/bin/ossutil" cp -r --update --jobs 4 \
    --include "*.webp" --exclude "._*" \
    --meta "Cache-Control:public,max-age=600" \
    assets/film-recommendation/ oss://highstrith-assets/assets/film-recommendation/ 2>&1 | tail -3 || fail "推荐卡封面上传失败"
  step "3b/8 线上封面自检"
  BAD=0
  for file in reel/img/*.webp; do
    name=$(basename "$file")
    code=$(curl -s -o /dev/null -w '%{http_code}' -I "https://highstrith-assets.oss-cn-hangzhou.aliyuncs.com/reel/img/$name")
    [ "$code" = "200" ] || { echo "  $code $name"; BAD=$((BAD+1)); }
  done
  for file in assets/film-recommendation/*.webp; do
    name=$(basename "$file")
    code=$(curl -s -o /dev/null -w '%{http_code}' -I "https://highstrith-assets.oss-cn-hangzhou.aliyuncs.com/assets/film-recommendation/$name")
    [ "$code" = "200" ] || { echo "  $code film-recommendation/$name"; BAD=$((BAD+1)); }
  done
  [ "$BAD" -eq 0 ] && echo "  全部 200" || fail "有 $BAD 张封面在 OSS 上不可访问，先别部署"
else
  step "3/8 上传 OSS — 跳过（--no-push）"
fi

step "4/8 重建页面并校验"
node scripts/build-framepick-library.mjs || fail "页面重建失败"
node scripts/check-framepick-library.mjs || fail "卡片校验未通过"

if [ "$FAST" = "0" ]; then
  step "5/8 全量测试（约 2 分钟）"
  ./scripts/run-framepick-tests.sh --standalone > /tmp/framepick-ship-tests.log 2>&1
  if [ $? -eq 0 ]; then
    grep -E '^Ran |^OK' /tmp/framepick-ship-tests.log | tail -2
  else
    grep -E '^(FAIL|ERROR):' /tmp/framepick-ship-tests.log | head -10
    fail "测试未通过，日志在 /tmp/framepick-ship-tests.log"
  fi
else
  step "5/8 全量测试 — 跳过（--fast）"
fi

step "6/8 同步橘生梦厂仓库与本地预览副本"
JS="/Volumes/E61--/网站/jusheng"
LIVE="/Volumes/E61--/网站/framepick-live"
JS_REMOTE="https://github.com/highstrith/jusheng.git"
[ -d "$JS" ] || fail "找不到 $JS（橘生梦厂独立仓库），先按 docs 里的拆站记录建好"
SYNC_OPTS=(-a --delete --exclude '/img/raw/' --exclude '._*' --exclude '.DS_Store'
  --exclude '/.git/' --exclude '/.github/' --exclude '/README.md' --exclude '/.gitignore' --exclude '/.nojekyll/')
rsync "${SYNC_OPTS[@]}" reel/ "$JS/"
find "$JS" -name '._*' -type f -delete 2>/dev/null
rsync "${SYNC_OPTS[@]}" reel/ "$LIVE/reel/"
find "$LIVE/reel" -name '._*' -type f -delete 2>/dev/null
JUSHENG_NEW=0
if git -C "$JS" diff --quiet && git -C "$JS" diff --cached --quiet; then
  echo "  橘生梦厂：产物无变化，跳过提交"
else
  git -C "$JS" add -A
  git -C "$JS" -c user.name="linjunjie" -c user.email="highstrith@gmail.com" commit -q -m "$MSG" || fail "橘生梦厂提交失败"
  echo "  橘生梦厂已提交 $(git -C "$JS" log --oneline -1)"
  JUSHENG_NEW=1
fi

step "7/8 提交并推送两站"
PORTFOLIO_DEPLOYED=0; JUSHENG_DEPLOYED=0
if git diff --quiet && git diff --cached --quiet; then
  echo "  作品集：没有文件改动，跳过提交与推送"
else
  git add -A
  git commit -q -m "$MSG" || fail "提交失败"
  echo "  作品集已提交 $(git log --oneline -1)"
  if [ "$PUSH" = "1" ]; then
    git push origin release/white-pages 2>&1 | tail -1 || fail "推送失败"
    git push origin HEAD:main 2>&1 | tail -1 || fail "推送 main 失败（没推 main 不会部署）"
    PORTFOLIO_DEPLOYED=1
  fi
fi
if [ "$PUSH" = "1" ] && [ "$JUSHENG_NEW" = "1" ]; then
  if ! git -C "$JS" remote get-url origin >/dev/null 2>&1; then
    git -C "$JS" remote add origin "$JS_REMOTE"
  fi
  git -C "$JS" push -u origin main 2>&1 | tail -1 || fail "橘生梦厂推送失败（仓库不存在就先到 GitHub 建 highstrith/jusheng）"
  JUSHENG_DEPLOYED=1
elif [ "$PUSH" = "1" ]; then
  echo "  橘生梦厂：没有新提交，不推送"
fi

if [ "$JUSHENG_DEPLOYED" = "1" ] || [ "$PORTFOLIO_DEPLOYED" = "1" ]; then
  step "8/8 等部署并复核线上"
  if [ "$JUSHENG_DEPLOYED" = "1" ]; then
    for _ in $(seq 1 12); do
      sleep 20
      S=$(curl -s "https://api.github.com/repos/highstrith/jusheng/actions/runs?per_page=1" \
        | python3 -c "import json,sys; d=json.loads(sys.stdin.read(),strict=False)['workflow_runs'][0]; print(d['status'], d['conclusion'])" 2>/dev/null)
      echo "  jusheng: $S"
      case "$S" in *success*|*failure*) break;; esac
    done
    case "$S" in
      *success*) ;;
      *) fail "橘生梦厂部署未成功（状态：$S）。到 Actions 看日志；若是 github-pages 产物相关报错，别点 Re-run failed jobs，直接 Run workflow 新开一次运行（见 docs/部署说明.md）" ;;
    esac
    sleep 5
    curl -s "https://highstrith.github.io/jusheng/?cb=$(date +%s)" -o /tmp/jusheng-live.html
    python3 - <<'PY'
import re, subprocess
h = open('/tmp/jusheng-live.html', encoding='utf-8').read()
cards = len(re.findall(r'<article class="card"', h))
srcs = sorted(set(re.findall(r'<img[^>]+src="([^"]+)"', h)))
bad = [s for s in srcs if subprocess.run(['curl','-s','-o','/dev/null','-w','%{http_code}','-I',s],
        capture_output=True, text=True).stdout.strip() != '200']
print(f'  橘生梦厂线上：{cards} 张卡片 · {len(srcs)} 张封面 · 破图 {len(bad)} 张')
for s in bad: print('    ', s)
PY
  fi
  if [ "$PORTFOLIO_DEPLOYED" = "1" ]; then
    for _ in $(seq 1 12); do
      sleep 20
      S=$(curl -s "https://api.github.com/repos/highstrith/highstrithstate/actions/runs?per_page=1" \
        | python3 -c "import json,sys; d=json.loads(sys.stdin.read(),strict=False)['workflow_runs'][0]; print(d['status'], d['conclusion'])" 2>/dev/null)
      echo "  作品集: $S"
      case "$S" in *success*|*failure*) break;; esac
    done
    case "$S" in
      *success*) ;;
      *) fail "作品集部署未成功（状态：$S）。到 Actions 看日志；若是 github-pages 产物相关报错，别点 Re-run failed jobs，直接 Run workflow 新开一次运行（见 docs/部署说明.md）" ;;
    esac
    sleep 5
    HTML=$(curl -s "https://highstrith.github.io/highstrithstate/?cb=$(date +%s)")
    echo "$HTML" | grep -q 'href="https://highstrith.github.io/jusheng/"' \
      && echo "  作品集首页：橘生梦厂入口链接在" \
      || fail "作品集首页没找到橘生梦厂入口链接"
    echo "$HTML" | grep -q 'assets/film-recommendation/xianggu-640w.webp' \
      && echo "  作品集首页：推荐封面已本地化" \
      || echo "  ! 作品集首页推荐封面引用有变，请人工看一眼"
  fi
else
  step "8/8 部署 — 跳过（--no-push 或无改动）"
fi

printf '\n\033[32m完成\033[0m\n'
