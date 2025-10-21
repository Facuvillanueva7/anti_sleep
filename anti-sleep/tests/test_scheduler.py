import types
import builtins
from scripts.anti_sleep import State, tick

class FakeCtrl:
    def __init__(self):
        self.moves = []
    def move(self, dx, dy):
        self.moves.append((dx, dy))

class Args(types.SimpleNamespace):
    pass

def test_no_jiggle_before_idle():
    args = Args(idle=10, interval=5, pixels=1, dry_run=True, verbose=False)
    st = State()
    ctrl = FakeCtrl()
    now = st.last_activity_ts + 9  # < idle
    did = tick(args, ctrl, st, now=now)
    assert did is False
    assert ctrl.moves == []

def test_jiggle_when_idle_and_interval_passed():
    args = Args(idle=10, interval=5, pixels=1, dry_run=True, verbose=False)
    st = State()
    ctrl = FakeCtrl()
    # Fuerza inactividad de 11s
    now = st.last_activity_ts + 11
    # Primera vez: debería jigglear
    did1 = tick(args, ctrl, st, now=now)
    assert did1 is True
    # Segunda llamada con solo 1s desde el último jiggle (interval=5): no jigglea
    did2 = tick(args, ctrl, st, now=now + 1)
    assert did2 is False
    # Pasado el intervalo: jigglea de nuevo
    did3 = tick(args, ctrl, st, now=now + 6)
    assert did3 is True
