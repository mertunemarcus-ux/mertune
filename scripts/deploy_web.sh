#!/bin/bash
# Mertune web deploy — always to project mertune-map, always verified.
# Usage: scripts/deploy_web.sh "what changed"
set -e
SRC=~/Projects/mertune/public/app.html
DIR=/tmp/vercel-mertune
MSG="${1:-deploy}"
mkdir -p "$DIR"
cp "$SRC" "$DIR/index.html"
cd "$DIR"
if ! grep -q '"projectName":"mertune-map"' .vercel/project.json 2>/dev/null; then
  rm -rf .vercel
  vercel link --yes --project mertune-map >/dev/null 2>&1
fi
grep -q '"projectName":"mertune-map"' .vercel/project.json || { echo "❌ not linked to mertune-map"; exit 1; }
STAMP="deploy-$(date +%s)"
sed -i '' "s#</head>#<!-- $STAMP -->\n</head>#" index.html
vercel --prod --yes 2>&1 | grep -m1 -E "Production|Error" || true
for i in 1 2 3 4 5 6; do
  sleep 5
  if curl -s -m 20 https://mertune-map.vercel.app | grep -q "$STAMP"; then
    echo "✅ live on https://mertune-map.vercel.app ($MSG)"; exit 0
  fi
done
echo "❌ deploy not visible on mertune-map.vercel.app after 30s"; exit 1
