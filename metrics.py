from collections import deque


class SessionMetrics:
    def __init__(self):
        self._current_get_streak: int = 0

    def record_get(self) -> int:
        self._current_get_streak += 1
        return self._current_get_streak

    def record_skip(self) -> None:
        self._current_get_streak = 0


class SampleMetrics:
    def __init__(self, window: int = 5000):
        self._samples: deque[float] = deque(maxlen=window)

    def record(self, duration_ms: float) -> None:
        self._samples.append(duration_ms)

    def report(self) -> dict:
        if not self._samples:
            return {"time": {"samples": 0}}
        samples = sorted(self._samples)
        n = len(samples)

        def pct(p: float) -> float:
            idx = p / 100 * (n - 1)
            lo = int(idx)
            hi = min(lo + 1, n - 1)
            return samples[lo] + (idx - lo) * (samples[hi] - samples[lo])

        return {
            "time": {
                "min_ms": round(samples[0], 2),
                "max_ms": round(samples[-1], 2),
                "mean_ms": round(sum(samples) / n, 2),
                "p50_ms": round(pct(50), 2),
                "p90_ms": round(pct(90), 2),
                "p95_ms": round(pct(95), 2),
                "samples": n,
            },
        }


class SessionMetrics:
    def __init__(self):
        self._current_get_streak: int = 0

    def record_get(self) -> int:
        self._current_get_streak += 1
        return self._current_get_streak

    def record_skip(self) -> None:
        self._current_get_streak = 0


class LoopMetrics:
    def __init__(self, window: int = 5000):
        self._samples: deque[float] = deque(maxlen=window)
        self._get_count: int = 0
        self._skip_count: int = 0
        self._max_get_streak: int = 0

    def record(self, duration_ms: float) -> None:
        self._samples.append(duration_ms)

    def record_get(self, streak: int) -> None:
        self._get_count += 1
        if streak > self._max_get_streak:
            self._max_get_streak = streak

    def record_skip(self) -> None:
        self._skip_count += 1

    def report(self) -> dict:
        if not self._samples:
            return {"time": {"samples": 0}}
        samples = sorted(self._samples)
        n = len(samples)

        def pct(p: float) -> float:
            idx = p / 100 * (n - 1)
            lo = int(idx)
            hi = min(lo + 1, n - 1)
            return samples[lo] + (idx - lo) * (samples[hi] - samples[lo])

        total = self._get_count + self._skip_count
        ratio = self._get_count / total if total > 0 else 0.0
        return {
            "time": {
                "min_ms": round(samples[0], 2),
                "max_ms": round(samples[-1], 2),
                "mean_ms": round(sum(samples) / n, 2),
                "p50_ms": round(pct(50), 2),
                "p90_ms": round(pct(90), 2),
                "p95_ms": round(pct(95), 2),
                "samples": n,
            },
            "get_count": self._get_count,
            "skip_count": self._skip_count,
            "get_vs_skip": ratio,
            "max_get_streak": self._max_get_streak,
        }
