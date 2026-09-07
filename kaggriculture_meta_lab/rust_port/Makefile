PYTHON ?= python3
CARGO ?= cargo
SEEDS ?= 64
THREADS ?= 4
GAMES ?= 64

.PHONY: build export test check benchmark framework-check

build:
	$(CARGO) build --release --locked

export:
	$(PYTHON) tools/export_tape.py -o work/example.json

test:
	$(CARGO) fmt --all -- --check
	$(CARGO) clippy --all-targets --locked -- -D warnings
	$(CARGO) test --locked
	$(CARGO) build --release --locked
	$(PYTHON) -m unittest discover -s tests -v

check: build
	$(PYTHON) tools/check.py --check --seeds $(SEEDS) --threads $(THREADS)

benchmark: build
	$(PYTHON) tools/benchmark.py --games $(GAMES) --threads $(THREADS) --repeats 3

# Opt-in network test. Install requirements-framework.txt in a venv first.
framework-check: build
	$(PYTHON) tools/check_framework.py --download
