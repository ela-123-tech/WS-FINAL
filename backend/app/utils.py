from __future__ import annotations
import asyncio, time

class Throttle:
    def __init__(self, min_interval_s: float = 1.0):
        self.min_interval_s = min_interval_s
        self._last = 0.0
        self._lock = asyncio.Lock()

    async def wait(self):
        async with self._lock:
            now = time.time()
            delta = now - self._last
            if delta < self.min_interval_s:
                await asyncio.sleep(self.min_interval_s - delta)
            self._last = time.time()
