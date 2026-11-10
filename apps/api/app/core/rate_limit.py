"""In-memory sliding-window limiter. Per-process: resets on restart and is not shared across workers.
Good enough for the local MVP; replace with a shared store before any multi-process deployment."""
import time
from collections import defaultdict, deque
from threading import Lock


class SlidingWindowLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def _prune(self, key: str, window: int, now: float) -> deque[float]:
        q = self._hits[key]
        while q and q[0] <= now - window:
            q.popleft()
        return q

    def add(self, key: str) -> None:
        with self._lock:
            self._hits[key].append(time.monotonic())

    def retry_after(self, key: str, max_hits: int, window: int) -> int | None:
        """Seconds to wait if the key is over its limit, otherwise None."""
        with self._lock:
            now = time.monotonic()
            q = self._prune(key, window, now)
            if len(q) >= max_hits:
                return max(1, int(q[0] + window - now) + 1)
            return None

    def clear(self, key: str) -> None:
        with self._lock:
            self._hits.pop(key, None)

    def reset_all(self) -> None:
        with self._lock:
            self._hits.clear()


login_limiter = SlidingWindowLimiter()
signup_limiter = SlidingWindowLimiter()
upload_limiter = SlidingWindowLimiter()
analyze_limiter = SlidingWindowLimiter()
research_limiter = SlidingWindowLimiter()
assessment_limiter = SlidingWindowLimiter()
coding_limiter = SlidingWindowLimiter()
feedback_limiter = SlidingWindowLimiter()
interview_limiter = SlidingWindowLimiter()
interview_ai_limiter = SlidingWindowLimiter()
report_limiter = SlidingWindowLimiter()
