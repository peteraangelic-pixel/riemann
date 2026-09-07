PYTHON      ?= .venv/bin/python
GAMES       ?= 4
OPPONENT    ?= pass
STEPS       ?= 720
SEED        ?= 0

.PHONY: help setup test match benchmark pack

help:
	@echo "make setup       - create venv and install kaggle-environments"
	@echo "make test        - run offline unit tests"
	@echo "make match       - local match vs OPPONENT=pass|random|self (GAMES, STEPS, SEED)"
	@echo "make benchmark   - quick 3-game benchmark vs each opponent at STEPS=360"
	@echo "make pack        - build submission.tar.gz (offline)"

setup:
	python3 -m venv .venv
	$(PYTHON) -m pip install -U pip
	$(PYTHON) -m pip install kaggle-environments

test:
	$(PYTHON) -m unittest discover -s tests -v

match:
	$(PYTHON) simulate.py --games $(GAMES) --opponent $(OPPONENT) --steps $(STEPS) --seed $(SEED)

benchmark:
	$(PYTHON) simulate.py --games 3 --opponent pass --steps 360 --seed 1
	$(PYTHON) simulate.py --games 3 --opponent random --steps 360 --seed 1

pack:
	rm -rf build_submission && mkdir -p build_submission
	cp agent.py build_submission/main.py
	tar -czf submission.tar.gz -C build_submission main.py
	rm -rf build_submission
	@echo "built submission.tar.gz"
