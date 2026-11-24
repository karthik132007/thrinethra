.PHONY: setup backend frontend test typecheck build evaluate model e2e migrate
setup:
	uv venv --python 3.12 .venv
	uv pip install --python .venv/bin/python -c requirements.lock -e '.[test,postgres]'
	npm --prefix apps/frontend ci
backend:
	.venv/bin/python scripts/run_backend.py
frontend:
	npm --prefix apps/frontend run dev
test:
	.venv/bin/python -m pytest -q
typecheck:
	npm --prefix apps/frontend run typecheck
build:
	npm --prefix apps/frontend run build
evaluate:
	.venv/bin/python evaluations/run.py
model:
	.venv/bin/python scripts/download_model.py
e2e:
	cd apps/frontend && npx playwright test
migrate:
	.venv/bin/alembic -c infrastructure/alembic.ini upgrade head
