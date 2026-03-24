PYTHON ?= python3.12
APP_MODULE ?= research_rag.api.app:create_app
PDF ?= /Users/revtiramantripathi/Downloads/ilovepdf_merged\ (2)\ (6).pdf
QUESTION ?= Summarize the key findings of this paper.

# Load .env if present
ifneq (,$(wildcard .env))
  include .env
  export
endif

.PHONY: install dev test lint format check run ingest query list-papers stats demo web-install web-dev docker-build

install:
	$(PYTHON) -m pip install -e .

dev:
	$(PYTHON) -m pip install -e .[dev]

test:
	$(PYTHON) -m unittest discover -s tests -v

lint:
	ruff check src tests

format:
	ruff format src tests

check:
	$(PYTHON) -m compileall src tests

run:
	PYTHONPATH=src $(PYTHON) -m uvicorn $(APP_MODULE) --factory --host 0.0.0.0 --port 8000 --reload

ingest:
	PYTHONPATH=src $(PYTHON) -m research_rag.cli ingest --pdf "$(PDF)"

query:
	PYTHONPATH=src $(PYTHON) -m research_rag.cli query --question "$(QUESTION)"

list-papers:
	PYTHONPATH=src $(PYTHON) -m research_rag.cli list-papers

stats:
	PYTHONPATH=src $(PYTHON) -m research_rag.cli stats

demo:
	streamlit run streamlit_app.py

web-install:
	cd web && npm install

web-dev:
	cd web && npm run dev

docker-build:
	docker build -t research-rag-service .
