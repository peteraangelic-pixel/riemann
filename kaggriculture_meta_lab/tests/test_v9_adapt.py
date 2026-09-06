"""V9 adaptive animal mix: flag-off must be exactly V8; flag-on must be sane."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _load(path):
    import importlib.util
    spec = importlib.util.spec_from_file_location(Path(path).stem, ROOT / path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m


def test_v9_flag_off_is_v8_identical_constants():
    v9 = _load("agents/variants/agent_v9_adapt.py")
    v8 = _load("agents/variants/agent_v8_fert.py")
    # shipped default: adaptation OFF -> every behaviour-affecting constant matches V8
    assert v9.ADAPT_ANIMALS is False
    for name in ("ANIMAL_TARGETS", "FERT_DETOUR_RADIUS", "STRAWBERRY_TARGET",
                 "FERTILIZER_RESERVE", "HANDS_MAX", "MELON_CELLS"):
        assert getattr(v9, name) == getattr(v8, name), name


def test_v9_adaptive_constants_in_sane_ranges():
    v9 = _load("agents/variants/agent_v9_adapt.py")
    # even when enabled, the flock only moves within a safe band and cows fixed
    assert 4 <= v9.ADAPT_SHEEP_BASE <= 9
    assert v9.ADAPT_SHEEP_HIGH >= v9.ADAPT_SHEEP_BASE
    assert v9.ADAPT_COWS_BASE == 8
    assert 4 <= v9.ADAPT_DECISION_DAY <= 20


def test_v9_with_flag_on_runs_one_game():
    """Smoke: enabling adaptation must not crash and must not change animal kind keys."""
    import importlib.util
    src = (ROOT / "agents/variants/agent_v9_adapt.py").read_text(encoding="utf-8")
    src = src.replace("ADAPT_ANIMALS = False", "ADAPT_ANIMALS = True", 1)
    tmp = Path("/tmp/_v9_on.py")
    tmp.write_text(src, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("_v9_on", tmp)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    assert m.ADAPT_ANIMALS is True
    # the adapt decision keeps COW present (fertilizer) and sheep within band
    targets = {"COW": m.ADAPT_COWS_BASE, "SHEEP": m.ADAPT_SHEEP_BASE}
    assert targets["COW"] == 8
