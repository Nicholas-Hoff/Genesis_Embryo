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


def test_pygad_mutation_records_each(monkeypatch):
    metrics_seq = [
        {"composite": 0.5, "cpu": 0, "memory": 0, "disk": 0, "network": 0},
        {"composite": 0.6, "cpu": 0, "memory": 0, "disk": 0, "network": 0},
    ]

    def fake_check():
        return metrics_seq.pop(0)

    monkeypatch.setattr(Health.SystemHealth, "check", staticmethod(fake_check))
    monkeypatch.setattr(Health.Survival, "score", lambda m: m)

    import PyGAD_Strategy

    class PygadMutator:
        def __init__(self):
            self.params = ["x", "y", "z"]
        def pick_strategy(self, meta_weights, is_stuck):
            return "pygad", types.SimpleNamespace(apply=PyGAD_Strategy.pygad_mutation)

    class PygadEmbryo:
        def __init__(self):
            self.param_bounds = {"x": (0.0, 2.0), "y": (0.0, 2.0), "z": (0.0, 2.0)}
            self.x = 1.0
            self.y = 1.0
            self.z = 1.0
            self.mutator = PygadMutator()
            self.db = types.SimpleNamespace(calls=[])
            def rec(**kw):
                self.db.calls.append(kw)
            self.db.record_mutation_context = rec

        def apply_param_bounds(self, param, value):
            low, high = self.param_bounds[param]
            return max(low, min(high, value))

    monkeypatch.setattr(PyGAD_Strategy.random, "sample", lambda seq, k: list(seq)[:2])

    embryo = PygadEmbryo()
    meta = {"pygad": 1.0, "reset": 0.0}

    Mutation.mutation_cycle(embryo, meta, stagnant_cycles=0)

    assert len(embryo.db.calls) == 2
    for call in embryo.db.calls:
        assert not isinstance(call["param"], list)


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
