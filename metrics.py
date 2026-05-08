from collections import deque


class LoopMetrics:
    def __init__(self, window: int = 300):
        self._samples: deque[float] = deque(maxlen=window)

    def record(self, duration_ms: float) -> None:
        self._samples.append(duration_ms)

    def report(self) -> dict:
        if not self._samples:
            return {"samples": 0}
        samples = sorted(self._samples)
        n = len(samples)

        def pct(p: float) -> float:
            idx = p / 100 * (n - 1)
            lo = int(idx)
            hi = min(lo + 1, n - 1)
            return samples[lo] + (idx - lo) * (samples[hi] - samples[lo])

        return {
            "min_ms": samples[0],
            "max_ms": samples[-1],
            "mean_ms": sum(samples) / n,
            "p50_ms": pct(50),
            "p90_ms": pct(90),
            "p95_ms": pct(95),
            "samples": n,
        }
