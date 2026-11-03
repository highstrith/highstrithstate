#!/bin/sh
# 把封面素材上传到 OSS（需先临时启用 RAM 子账号 oss-uploader 的 AccessKey）。
#
#   scripts/upload-cover-assets.sh            上传 reel/img 下的 webp
#   scripts/upload-cover-assets.sh --dry-run  只列出会传什么
#
# 前提：`~/bin/ossutil` 已配好（ossutil config，endpoint 用 oss-cn-hangzhou）。
# 用完记得在 RAM 控制台禁用 AccessKey，并删除本机配置。
set -e
cd "$(dirname "$0")/.."

OSSUTIL="${OSSUTIL:-$HOME/bin/ossutil}"
BUCKET="${BUCKET:-oss://highstrith-assets/reel/img/}"

if [ ! -x "$OSSUTIL" ]; then
  echo "找不到 ossutil：$OSSUTIL" >&2
  exit 2
fi

# ossutil 没有 --dry-run，这里只把待传清单打出来。
if [ "$1" = "--dry-run" ]; then
  echo "待上传（reel/img/*.webp，raw/ 除外）："
  for file in reel/img/*.webp; do
    printf '  %6sKB  %s\n' "$(( $(wc -c < "$file") / 1024 ))" "$(basename "$file")"
  done
  exit 0
fi

# 只传 webp 封面；raw/ 是平台原图缓存，属于母版，不进 OSS。
# 素材不是哈希命名，Cache-Control 与 HTML 对齐 600 秒，换图最多 10 分钟生效。
"$OSSUTIL" cp -r --update --jobs 4 \
  --include "*.webp" --exclude "raw/*" \
  --meta "Cache-Control:public,max-age=600" \
  reel/img/ "$BUCKET"

echo
echo "上传后逐个确认（应全部 200）："
for file in reel/img/*.webp; do
  name=$(basename "$file")
  code=$(curl -s -o /dev/null -w '%{http_code}' -I "https://highstrith-assets.oss-cn-hangzhou.aliyuncs.com/reel/img/$name")
  printf '  %s %s\n' "$code" "$name"
done
