import importlib.util
from pathlib import Path

from kaggriculture_lab.rust_backend import _source

PATH = Path(__file__).parents[1] / "agents/candidates/champion_tape_germanjurado1.py"
ALT_PATH = Path(__file__).parents[1] / "agents/candidates/champion_tape_germanjurado1_ep107212592.py"
TOP7_KANNO_PATH = Path(__file__).parents[1] / "agents/candidates/top7_kanno_ep107377838.py"
TOP7_KANNO_BEST_PATH = Path(__file__).parents[1] / "agents/candidates/top7_kanno_bestsub_ep107384200.py"


def test_candidate_is_audited_static_tape_with_correct_replay_offset_length():
    compiled = _source(str(PATH))
    assert compiled is not None
    assert compiled.trim_hands
    assert len(compiled.actions) == 2
    assert all(len(stream) == 719 for stream in compiled.actions)
    assert compiled.actions[0][0]["market"] == [["BUY_PRODUCT", "WHEAT", 5]]


def test_alternate_episode_candidate_has_the_same_audited_contract():
    for path in (ALT_PATH, TOP7_KANNO_PATH, TOP7_KANNO_BEST_PATH):
        compiled = _source(str(path))
        assert compiled is not None and compiled.trim_hands
        assert len(compiled.actions) == 2
        assert all(len(stream) == 719 for stream in compiled.actions)


def test_candidate_adapts_only_hand_count():
    spec = importlib.util.spec_from_file_location("germanjurado_candidate", PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    obs = {"player": 0, "step": 1, "farms": [{"hands": []}, {"hands": []}]}
    action = module.agent(obs, {})
    assert action["hands"] == []
    assert action["market"][0] == ["BUY_PRODUCT", "WHEAT", 85]
