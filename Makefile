.PHONY: help init up down restart logs status api-test web-check config

help:
	@echo "CloudSec Range development commands:"
	@echo "  make init       Create local .env from .env.example"
	@echo "  make config     Validate Docker Compose configuration"
	@echo "  make up         Build and start the local stack"
	@echo "  make down       Stop the local stack (keeps data volumes)"
	@echo "  make restart    Restart the local stack"
	@echo "  make logs       Follow service logs"
	@echo "  make status     Show container status"
	@echo "  make api-test   Run API tests inside the container"
	@echo "  make web-check  Run frontend TypeScript check inside the container"

init:
	@test -f .env || cp .env.example .env
	@echo "Created .env if it did not exist. Edit it and replace both placeholder passwords."

config:
	docker compose config --quiet

up:
	docker compose up --build -d

down:
	docker compose down

restart:
	docker compose restart

logs:
	docker compose logs -f --tail=100

status:
	docker compose ps

api-test:
	docker compose exec api pytest -q

web-check:
	docker compose exec web npm run typecheck
