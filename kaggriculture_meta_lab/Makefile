PYTHON ?= .venv/bin/python
WORKERS ?= 16
GAMES ?= 200

.PHONY: setup test smoke tournament corpus rate clean

setup:
	python3 -m venv .venv
	$(PYTHON) -m pip install -U pip
	$(PYTHON) -m pip install -r requirements.txt

test:
	$(PYTHON) -m pytest -q

smoke:
	$(PYTHON) scripts/run_tournament.py --candidate starter --opponent pass=pass \
		--games 8 --workers 8
	$(PYTHON) scripts/run_corpus.py --candidate starter --corpus corpus/sample \
		--team __none__ --workers 8 --limit 3

tournament:
	$(PYTHON) scripts/run_tournament.py --candidate agents/ref/agent_v7.py \
		--opponent starter=starter --opponent v4=agents/ref/agent_v4.py \
		--games $(GAMES) --workers $(WORKERS) --gate

corpus:
	$(PYTHON) scripts/run_corpus.py --candidate agents/ref/agent_v7.py \
		--corpus corpus/sample --team "Lauresowe" --workers $(WORKERS)

rate:
	$(PYTHON) scripts/rate.py --agents v7=agents/ref/agent_v7.py \
		--agents v4=agents/ref/agent_v4.py --agents starter=starter \
		--games 60 --workers $(WORKERS)

clean:
	rm -rf reports/*.json reports/*.csv artifacts/* __pycache__
