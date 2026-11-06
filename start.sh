#!/usr/bin/env bash
# Run gym-guy locally and keep it up to date.
#
# Layout (both repos side by side):
#   ~/Desktop/gym-guy/gym-guy-back   <- this repo (Django API on :8000, SQLite)
#   ~/Desktop/gym-guy/gym-guy-front  <- React app on :5173
#
# Every start pulls both repos. While running, it pulls again every 2 minutes;
# Django and Vite reload by themselves, and new migrations or packages are installed.
# Needs: Python 3.10+, Node 20+, git.  Stop with Ctrl+C.
set -euo pipefail
BACK="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$BACK")"
FRONT="$ROOT/gym-guy-front"
PULL_EVERY="${PULL_EVERY:-120}"

command -v node >/dev/null 2>&1 || { echo "✗ Node.js نصب نیست. نسخه ۲۰ به بالا را از https://nodejs.org نصب کنید."; exit 1; }
[ "$(node -p 'process.versions.node.split(".")[0]')" -ge 20 ] || { echo "✗ Node $(node -v) قدیمی است؛ نسخه ۲۰ به بالا لازم است."; exit 1; }
if [ ! -d "$FRONT/.git" ]; then
  echo "▶ cloning gym-guy-front next to this folder…"
  git clone https://github.com/alihanii/gym-guy-front.git "$FRONT"
fi

pull() {  # pull <dir>; prints the files that changed
  local dir="$1" before
  before="$(git -C "$dir" rev-parse HEAD 2>/dev/null || echo none)"
  git -C "$dir" pull --ff-only -q 2>/dev/null || { echo "⚠ git pull failed in $(basename "$dir") (local changes?)" >&2; return 0; }
  [ "$before" = "$(git -C "$dir" rev-parse HEAD)" ] || git -C "$dir" diff --name-only "$before" HEAD
}

backend_setup() {
  cd "$BACK"
  . .venv/bin/activate
  pip install -q -r requirements.txt
  python manage.py migrate -v0
  python manage.py import_exercise_list >/dev/null
}

echo "▶ updating from GitHub…"
pull "$BACK" >/dev/null
pull "$FRONT" >/dev/null

echo "▶ backend (SQLite)…"
cd "$BACK"
[ -f .env ] || cp .env.example .env
[ -d .venv ] || python3 -m venv .venv
. .venv/bin/activate
pip install -q -r requirements.txt
python manage.py migrate -v0
python manage.py seed_exercises
if [ ! -f .cache/fedb-imported ]; then
  [ -d .cache/free-exercise-db ] || { echo "▶ downloading exercise images (free-exercise-db, public domain)…"; git clone --depth 1 https://github.com/yuhonas/free-exercise-db.git .cache/free-exercise-db; }
  python manage.py import_free_exercise_db .cache/free-exercise-db --images
  touch .cache/fedb-imported
fi
python manage.py import_exercise_list
python manage.py runserver 127.0.0.1:8000 &
PIDS=($!)

cd "$FRONT"
echo "▶ frontend: npm install…"
npm install --no-audit --no-fund
npm run dev -- --port 5173 --strictPort &
PIDS+=($!)

(
  while sleep "$PULL_EVERY"; do
    changed="$(pull "$BACK")"
    if [ -n "$changed" ]; then
      echo "↻ backend updated"
      (backend_setup) || echo "⚠ backend update step failed"
    fi
    changed="$(pull "$FRONT")"
    if [ -n "$changed" ]; then
      echo "↻ frontend updated"
      if grep -q "package" <<<"$changed"; then (cd "$FRONT" && npm install --no-audit --no-fund -s) || true; fi
    fi
  done
) &
PIDS+=($!)
trap 'kill "${PIDS[@]}" 2>/dev/null; exit 0' INT TERM EXIT

echo
echo "✓ open http://localhost:5173   (updates are pulled every ${PULL_EVERY}s; Ctrl+C to stop)"
wait
