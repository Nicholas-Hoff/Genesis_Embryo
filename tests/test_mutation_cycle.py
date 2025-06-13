import types
import pytest

import Mutation
import Health

class DummyStrategy:
    def apply(self, embryo):
        old = getattr(embryo, "val", 0)
        setattr(embryo, "val", old + 1)
        return "inc", {"param": "val", "old": old, "new": old + 1}

class DummyMutator:
    def pick_strategy(self, meta_weights, is_stuck):
        return "gaussian", DummyStrategy()

class DummyDB:
    def __init__(self):
        self.last = None
    def record_mutation_context(self, **kwargs):
        self.last = kwargs

class DummyEmbryo:
    def __init__(self):
        self.val = 0
        self.mutator = DummyMutator()
        self.db = DummyDB()


def test_mutation_cycle_updates_score_and_weights(monkeypatch):
    metrics_seq = [
        {"composite": 0.5, "cpu": 0, "memory": 0, "disk": 0, "network": 0},
        {"composite": 0.6, "cpu": 0, "memory": 0, "disk": 0, "network": 0},
    ]
    def fake_check():
        return metrics_seq.pop(0)
    monkeypatch.setattr(Health.SystemHealth, "check", staticmethod(fake_check))
    monkeypatch.setattr(Health.Survival, "score", lambda m: m)

    embryo = DummyEmbryo()
    meta = {"gaussian": 1.0, "reset": 0.0}

    new_score, new_stagnant, strategy = Mutation.mutation_cycle(
        embryo, meta, stagnant_cycles=0, return_strategy=True
    )

    assert new_score == pytest.approx(0.6)
    assert new_stagnant == 0
    assert strategy == "gaussian"
    assert embryo.val == 1
    assert meta["gaussian"] > 0.9
