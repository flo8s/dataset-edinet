#!/usr/bin/env bash
set -euo pipefail
target="${1:-local}"
# documents は日付単位の増分取得のため、公開済みカタログを取り込んでから
# 未取得日のみ取得する（初回は未公開なので無視）。
uv run fdl pull "$target" || true
exec "$(dirname "$0")/../shared/scripts/build-dataset.sh" "$target"
