.PHONY: setup backend frontend test typecheck build evaluate model e2e migrate
setup:
	uv venv --python 3.12 --allow-existing .venv
	uv pip install --python .venv/bin/python torch torchvision --index-url https://download.pytorch.org/whl/cpu
	uv pip install --python .venv/bin/python -c requirements.lock -e '.[vision,test,postgres]'
	npm --prefix apps/frontend ci
	.venv/bin/python scripts/download_assets.py
	.venv/bin/python scripts/prepare_real_demo.py
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
	.venv/bin/python evaluations/real_video.py
model:
	.venv/bin/python scripts/download_assets.py --models-only
e2e:
	cd apps/frontend && PLAYWRIGHT_BROWSERS_PATH=$(CURDIR)/runtime/browsers npx playwright test
migrate:
	.venv/bin/alembic -c infrastructure/alembic.ini upgrade head

assets:
	.venv/bin/python scripts/download_assets.py
real-demo:
	.venv/bin/python scripts/prepare_real_demo.py
real-evaluate:
	.venv/bin/python evaluations/real_video.py
run:
	.venv/bin/python scripts/run.py
llm:
	OLLAMA_NO_CLOUD=1 OLLAMA_MODELS=$(CURDIR)/runtime/models/ollama OLLAMA_HOST=127.0.0.1:11435 ollama serve
llm-model:
	OLLAMA_HOST=127.0.0.1:11435 ollama pull qwen2.5:1.5b
browser-install:
	cd apps/frontend && PLAYWRIGHT_BROWSERS_PATH=$(CURDIR)/runtime/browsers npx playwright install chromium

physical-evaluate:
	.venv/bin/python evaluations/physical_cameras.py

synthetic-evaluate:
	.venv/bin/python evaluations/run.py
