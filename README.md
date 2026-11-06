# gym-guy-back

Django + DRF API for gym-guy (Persian, RTL workout logger and coach portal).
The React app lives in [gym-guy-front](https://github.com/alihanii/gym-guy-front).

## Run on a Mac (both repos, auto-updating)

```bash
mkdir -p ~/Desktop/gym-guy && cd ~/Desktop/gym-guy
git clone https://github.com/alihanii/gym-guy-back.git
git clone https://github.com/alihanii/gym-guy-front.git
./gym-guy-back/start.sh
```

Open http://localhost:5173. `start.sh` pulls both repos on every start and every
2 minutes while running, then migrates and reinstalls packages when needed.
Next time just run `~/Desktop/gym-guy/gym-guy-back/start.sh`.

Needs Python 3.10+, Node 20+ and git. Local runs use SQLite (`db.sqlite3`);
on the server set `DATABASE_URL` to PostgreSQL in `.env` (see `.env.example`).

## Backend only

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
python manage.py test tests
```

The exercise bank comes from `data/exercises.csv` (English name, Persian title,
muscle group, image). Edit that file and restart; see `data/README.md`.
`python manage.py import_exercise_list --images` loads it by hand.
