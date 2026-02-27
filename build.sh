#!/bin/bash
# 自动构建脚本：读取 章节/*.md，生成 dist/index.html，并可选部署
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
CHAPTER_DIR="$DIR/章节"
DIST_DIR="$DIR/dist"
OUTPUT="$DIST_DIR/index.html"

mkdir -p "$DIST_DIR"

# 用 python3 来处理 markdown -> HTML 转换和模板生成
python3 "$DIR/build.py"

echo "✅ 构建完成: $OUTPUT"

# 如果传入 --deploy 参数，自动部署
if [ "$1" = "--deploy" ]; then
  echo "📤 部署到 Cloudflare Pages..."
  cd "$DIR"
  npx wrangler pages deploy dist --project-name chongsheng2008 --commit-dirty=true
  echo "✅ 部署完成"
fi
