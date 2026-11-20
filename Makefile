.PHONY: dev test lint typecheck build docker reset

dev:            ## Sobe API + painel em modo desenvolvimento
	./start.sh

test:           ## Testes do backend
	cd backend && .venv/bin/pytest

lint:           ## Lint do backend
	cd backend && .venv/bin/ruff check app tests

typecheck:      ## Checagem de tipos do frontend
	cd frontend && npx tsc -b

build:          ## Build de produção do frontend
	cd frontend && npm run build

docker:         ## Sobe tudo via Docker em http://localhost:8080
	docker compose up --build

reset:          ## Apaga o banco local (é recriado com dados de demo no próximo start)
	rm -f backend/omniflow.db*
