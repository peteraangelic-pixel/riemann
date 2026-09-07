"""Pytest anchor for the lab.

Adds the lab root to sys.path so `import kaggriculture_lab...` and
`from scripts... import ...` work in tests. Collection scope is handled by
pytest.ini's `testpaths = tests`, which keeps a nested duplicate copy of the
lab (e.g. a downloaded "LAB centralny" subfolder) from being collected and
triggering an "import file mismatch" error on same-named test modules.
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
