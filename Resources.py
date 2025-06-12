# resources.py

import threading
import time
import psutil
from typing import Optional

class CPUThrottler:
    __slots__ = (
        '_limit', '_interval', '_stop_evt', '_last_reset', 
        '_accum_busy', '_prev_cpu', '_thread'
    )

    def __init__(self, limit_pct: float, interval: float = 1.0) -> None:
        self._limit      = max(0.0, min(limit_pct, 100.0))
        self._interval   = interval
        self._stop_evt   = threading.Event()
        self._last_reset = time.perf_counter()
        self._accum_busy = 0.0

        # initialize prev_cpu so first delta is zero
        proc = psutil.Process()
        self._prev_cpu = sum(proc.cpu_times()[:2])

        # keep a reference so we can join later if we want
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_evt.set()
        if self._thread:
            self._thread.join()

    def _run(self) -> None:
        proc = psutil.Process()
        while not self._stop_evt.is_set():
            now     = time.perf_counter()
            elapsed = now - self._last_reset

            if elapsed >= self._interval:
                self._last_reset = now
                self._accum_busy = 0.0
                elapsed = 0.0

            busy_target = (self._limit / 100.0) * self._interval

            # measure CPU time since last loop
            used_cpu   = sum(proc.cpu_times()[:2])
            delta_busy = used_cpu - self._prev_cpu
            self._prev_cpu = used_cpu

            to_burn = busy_target - delta_busy
            if to_burn > 0:
                # split spin/sleep to approximate duty-cycle
                t0 = time.perf_counter()
                while time.perf_counter() - t0 < to_burn * 0.5:
                    pass
                time.sleep(to_burn * 0.5)
            else:
                # over budget: sleep until next window
                time.sleep(self._interval - elapsed)


class RAMBurner:
    __slots__ = ('_limit', '_chunk', '_interval', '_buffer', '_stop_evt', '_thread')

    def __init__(self, limit_pct: float, chunk_mb: int = 10, interval: float = 1.0) -> None:
        self._limit    = max(0.0, min(limit_pct, 100.0))
        self._chunk    = chunk_mb * 1024 * 1024
        self._interval = interval
        self._buffer   = []
        self._stop_evt = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_evt.set()
        if self._thread:
            self._thread.join()

    def _run(self) -> None:
        vm = psutil.virtual_memory
        while not self._stop_evt.is_set():
            used = vm().percent
            if used < self._limit:
                try:
                    self._buffer.append(bytearray(self._chunk))
                except MemoryError:
                    time.sleep(self._interval)
            else:
                time.sleep(self._interval)


def spawn_resource_controllers(
    cpu_pct: Optional[float], 
    ram_pct: Optional[float]
) -> list:
    """
    Start CPU- and/or RAM- controllers as daemons.
    Returns controller objects, so you can .stop() them later.
    """
    controllers = []
    if cpu_pct:
        cpu = CPUThrottler(limit_pct=cpu_pct)
        cpu.start()
        controllers.append(cpu)
    if ram_pct:
        ram = RAMBurner(limit_pct=ram_pct)
        ram.start()
        controllers.append(ram)
    return controllers
