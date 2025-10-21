#!/usr/bin/env python3
"""
anti_sleep.py — Evita que la compu entre en reposo moviendo el mouse levemente
cuando no hay actividad humana por X segundos.

Requisitos:  pip install -r requirements.txt
Uso:
  python scripts/anti_sleep.py --idle 120 --interval 30 --pixels 1 --verbose
  # modo sin mover mouse real (para Codespaces / pruebas):
  python scripts/anti_sleep.py --idle 10 --interval 5 --dry-run --verbose
"""

import argparse
import random
import time
from datetime import datetime
from threading import Lock, Thread

try:
    from pynput import mouse, keyboard
except ImportError:
    mouse = keyboard = None  # Permitimos --dry-run sin pynput


def parse_args():
    p = argparse.ArgumentParser(description="Anti-sleep por inactividad")
    p.add_argument("--idle", type=int, default=120,
                   help="Segundos sin actividad para empezar a mover (default 120)")
    p.add_argument("--interval", type=int, default=30,
                   help="Segundos entre jiggles mientras siga inactiva (default 30)")
    p.add_argument("--pixels", type=int, default=1,
                   help="Píxeles por jiggle (ida y vuelta) (default 1)")
    p.add_argument("--verbose", action="store_true", help="Mostrar logs")
    p.add_argument("--dry-run", action="store_true",
                   help="No mover el mouse; solo loguear (útil para test)")
    return p.parse_args()


class State:
    def __init__(self):
        self.last_activity_ts = time.monotonic()
        self.last_jiggle_ts = 0.0
        self.lock = Lock()


def mark_activity(state: State):
    with state.lock:
        state.last_activity_ts = time.monotonic()


def safe_move(ctrl, dx, dy):
    try:
        ctrl.move(dx, dy)
    except Exception:
        # No queremos romper el loop por fallas del SO/permiso
        pass


def do_jiggle(args, ctrl, *, now, state: State, rng=random):
    """Mueve ida y vuelta y devuelve True si jiggleó."""
    dx = args.pixels * rng.choice((-1, 1))
    dy = 0
    if not args.dry_run:
        safe_move(ctrl, dx, dy)
        time.sleep(0.05)
        safe_move(ctrl, -dx, -dy)
    if args.verbose:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Jiggle (idle {int(now - state.last_activity_ts)}s)")
    return True


def tick(args, ctrl, state: State, *, now=None):
    """
    Ejecuta una 'evaluación' del scheduler: decide si jigglear o no.
    Devuelve True si jiggleó, False si no.
    (Separado para poder testear con tiempo simulado.)
    """
    now = time.monotonic() if now is None else now
    with state.lock:
        idle_for = now - state.last_activity_ts
        since_last_jiggle = now - state.last_jiggle_ts

    if idle_for >= args.idle and since_last_jiggle >= args.interval:
        did = do_jiggle(args, ctrl, now=now, state=state)
        with state.lock:
            state.last_jiggle_ts = now
        return did
    return False


def run(args):
    state = State()

    # Listeners (solo si no es dry-run y hay pynput disponible)
    m_listener = k_listener = None
    ctrl = None

    if not args.dry_run:
        if mouse is None or keyboard is None:
            print("Falta 'pynput'. Instala con: pip install -r requirements.txt")
            return 2

        def on_mouse_move(x, y): mark_activity(state)
        def on_mouse_click(x, y, b, p): mark_activity(state)
        def on_mouse_scroll(x, y, dx, dy): mark_activity(state)
        def on_key_press(key): mark_activity(state)
        def on_key_release(key): mark_activity(state)

        m_listener = mouse.Listener(
            on_move=on_mouse_move,
            on_click=on_mouse_click,
            on_scroll=on_mouse_scroll
        )
        k_listener = keyboard.Listener(
            on_press=on_key_press,
            on_release=on_key_release
        )
        m_listener.start()
        k_listener.start()
        ctrl = mouse.Controller()
    else:
        # Control dummy para pruebas (cumple interfaz .move)
        class DummyCtrl:
            def move(self, dx, dy): pass
        ctrl = DummyCtrl()

    if args.verbose:
        mode = "DRY-RUN" if args.dry_run else "NORMAL"
        print(f"Anti-sleep activo ({mode}). Ctrl+C para salir.")
        print(f"Idle: {args.idle}s | Intervalo: {args.interval}s | Pixels: {args.pixels}")

    try:
        while True:
            tick(args, ctrl, state)
            time.sleep(0.5)
    except KeyboardInterrupt:
        if args.verbose:
            print("\nCerrando...")
    finally:
        if m_listener: m_listener.stop()
        if k_listener: k_listener.stop()

    return 0


if __name__ == "__main__":
    exit(run(parse_args()))
