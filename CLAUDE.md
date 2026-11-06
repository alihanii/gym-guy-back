# Gym Guy — notes for Claude

> This repo is the backend only (former `backend/` folder). The React app is in the gym-guy-front repo, cloned next to it. Paths below that start with `backend/` are now at the repo root; `frontend/` paths live in gym-guy-front. Run both with `./start.sh`.

- Monorepo: `backend/` (Django 5 + DRF; SQLite locally, PostgreSQL in prod via DATABASE_URL; JSONField for lists, no contrib.postgres, media on S3 via django-storages) and `frontend/` (Vite + React + TS, RTL Persian).
- UI work: use the design skills installed in `.claude/skills/` — `impeccable` (Operate mode for app screens; read `reference/craft-floor.md` before editing UI), `emil-design-eng` and its sibling animation skills, `ui-ux-pro-max`, and `taste-skill` (marketing pages only).
- Design tokens and rules live in `DESIGN.md` and `frontend/src/index.css`. Dark-first, Vazirmatn, Persian digits via `fa()`, tabular numbers.
- Backend tests: `cd backend && python manage.py test tests`. Frontend type check: `cd frontend && npx tsc -b`.
- The exercise bank in `backend/apps/exercises/seed_data.py` is original. Do not scrape third-party apps' private APIs.
