"""In-process login attempt limiter for single-instance internal development.

Not suitable for multi-worker production deployments; use shared Redis or
database-backed throttling before exposing owner login publicly.
"""
import threading
import time
from collections import defaultdict, deque


class LoginRateLimiter:
    def __init__(self, max_attempts: int = 5, window_seconds: int = 300):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._attempts = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str, *, now: float | None = None) -> bool:
        current = time.monotonic() if now is None else now
        with self._lock:
            attempts = self._attempts[key]
            while attempts and attempts[0] <= current - self.window_seconds:
                attempts.popleft()
            if len(attempts) >= self.max_attempts:
                return False
            attempts.append(current)
            return True


login_limiter = LoginRateLimiter()
