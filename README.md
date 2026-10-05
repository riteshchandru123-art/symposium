# AI College Symposium Assistant

## Local dev (no Docker, fastest for backend iteration)

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate          # uses SQLite by default
python manage.py seed_data
python manage.py createsuperuser
python manage.py runserver
```
Visit http://localhost:8000/admin

## Local dev with Docker (Postgres, matches production)

```bash
cp .env.example .env              # fill in DJANGO_SECRET_KEY at minimum
docker compose up --build
```
This runs Postgres + Django together. Migrations run automatically on startup.
To seed data inside the container:
```bash
docker compose exec web python manage.py seed_data
docker compose exec web python manage.py createsuperuser
```

## Deploying to AWS

Two straightforward options depending on how much you want to manage:

**Option A — EC2 (simplest, full control)**
1. Launch a small EC2 instance (t3.small is enough for a demo), Ubuntu AMI.
2. Install Docker + Docker Compose on the instance.
3. Clone the repo, copy `.env.example` to `.env` with real production values
   (`DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS=<your-ec2-public-ip-or-domain>`,
   a real random `DJANGO_SECRET_KEY`, real DB password).
4. `docker compose up --build -d`
5. Open port 8000 (or put Nginx in front on port 80) in the instance's security group.
6. For production, swap the `web` service command in docker-compose to use
   `gunicorn symposium_project.wsgi:application --bind 0.0.0.0:8000` instead of
   `runserver` (already set as the Dockerfile's default CMD — just drop the
   `command:` override in docker-compose.yml for the prod deploy).

**Option B — Elastic Beanstalk (less manual server management)**
1. `eb init` in the project root, choose Docker platform.
2. `eb create symposium-env`
3. Set environment variables (same as `.env`) via `eb setenv` or the console.
4. Point Beanstalk at RDS Postgres instead of a Docker Postgres container —
   more durable for anything beyond a demo.

Since you already know AWS, pick whichever you're fastest with — the app itself
doesn't care, it just needs `DB_ENGINE=postgres` and the `DB_*` env vars pointed
at wherever Postgres lives (container, RDS, etc).

**Don't wait until the last day to deploy.** Get a rough version live by Day 3-4
even before the agent/RAG pieces are finished, so deployment problems surface
early rather than during final integration.

## Project structure

```
symposium/
├── core/                   # Django app: models, admin, seed data
│   ├── models.py           # Venue, Speaker, Session, Registration
│   ├── admin.py
│   └── management/commands/seed_data.py
├── rag/                    # RAG pipeline (see rag/README or prior handoff)
│   ├── documents/          # FAQ, bios, policies - source text for RAG
│   ├── build_index.py
│   └── search.py
├── symposium_project/      # Django settings/urls
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── requirements.txt
```

## Environment variables

See `.env.example` for the full list. Copy it to `.env` (which is gitignored)
and fill in real values before running.
