# Local Development Operations

## WSL 2 guidance

Keep source code under the Linux filesystem (for example `~/projects/cloudsec-range`). Avoid working from `/mnt/c` for dependency-heavy Node/Python projects unless necessary.

## Start

```bash
cp .env.example .env
# Edit .env and replace placeholder values.
docker compose config --quiet
docker compose up --build -d
docker compose ps
```

## Verify

```bash
curl -fsS http://localhost:8000/health/live
curl -fsS http://localhost:8000/health/ready
curl -fsS http://localhost:8000/api/v1/system/info
```

Open `http://localhost:3000` and `http://localhost:8000/docs`.

## Stop and retain data

```bash
docker compose down
```

## Destructive reset

`docker compose down -v` deletes named database/cache volumes. Use only when intentionally wiping the local development data.

## Troubleshooting

- `address already in use`: inspect `ss -ltnp` and change `WEB_PORT`, `API_PORT`, `POSTGRES_PORT` or `REDIS_PORT` in `.env`.
- API not ready: inspect `docker compose logs api db redis`.
- Frontend cannot reach API: confirm API container health and `API_INTERNAL_URL=http://api:8000`.
- Database credentials changed after first startup: update `.env`; changing environment variables does not change the password in an already initialized PostgreSQL data volume. Use a controlled password rotation procedure rather than deleting data.

## Curriculum Engine update (additive migration)

Before applying a database migration to an existing local installation, take a backup:

```bash
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' > "$HOME/cloudsec-range-before-curriculum.sql"
```

Then rebuild and restart the API and web application:

```bash
docker compose config --quiet
docker compose up -d --build api web
docker compose logs --tail=120 api
```

The API startup command applies Alembic migrations and then runs the idempotent curriculum import. Verify the new catalogue:

```bash
curl -fsS http://localhost:8000/api/v1/curriculum/catalog
curl -fsS http://localhost:8000/api/v1/curriculum/coverage/summary
```

Open `http://localhost:3000/learning` for the imported map. The existing PostgreSQL named volume is reused. Do not run `docker compose down -v` for this update.
