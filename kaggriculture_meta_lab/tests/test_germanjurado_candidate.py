import importlib.util
from pathlib import Path

from kaggriculture_lab.rust_backend import _source

PATH = Path(__file__).parents[1] / "agents/candidates/champion_tape_germanjurado1.py"


def test_candidate_is_audited_static_tape_with_correct_replay_offset_length():
    compiled = _source(str(PATH))
    assert compiled is not None
    assert compiled.trim_hands
    assert len(compiled.actions) == 2
    assert all(len(stream) == 719 for stream in compiled.actions)
    assert compiled.actions[0][0]["market"] == [["BUY_PRODUCT", "WHEAT", 5]]


def test_candidate_adapts_only_hand_count():
    spec = importlib.util.spec_from_file_location("germanjurado_candidate", PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    obs = {"player": 0, "step": 1, "farms": [{"hands": []}, {"hands": []}]}
    action = module.agent(obs, {})
    assert action["hands"] == []
    assert action["market"][0] == ["BUY_PRODUCT", "WHEAT", 85]
