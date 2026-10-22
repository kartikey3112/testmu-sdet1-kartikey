# Each target is a thin wrapper; the README lists the raw command for each one.
PY ?= python
MODULE ?= login
VERSION ?= v1
RUN ?=

.PHONY: setup app reset-db test test-ui test-api generate gherkin prompts-md traceability classify eval lint

setup:
	$(PY) -m pip install -r requirements.txt
	$(PY) -m playwright install chromium

app:
	$(PY) -m uvicorn app.main:app --reload

reset-db:
	$(PY) -m app.seed

test:
	$(PY) -m pytest

test-ui:
	$(PY) -m pytest -m ui

test-api:
	$(PY) -m pytest -m api

generate:
	$(PY) -m scripts.generate_tests --module $(MODULE) --version $(VERSION)

gherkin:
	$(PY) -m ai.testgen.to_gherkin

prompts-md:
	$(PY) -m scripts.build_prompts_md

traceability:
	$(PY) -m scripts.build_traceability

classify:
	$(PY) -m ai.classifier.classify --run $(RUN)

eval:
	$(PY) -m scripts.eval_classifier

lint:
	$(PY) -m ruff check .
