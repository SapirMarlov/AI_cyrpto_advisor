import time
from collections import defaultdict


class LoginRateLimiter:
    """Limit failed login attempts by IP and email."""

    def __init__(self, max_attempts: int, window_seconds: int):
        """Set the max attempts and time window."""
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._attempts: dict[tuple[str, str], list[float]] = defaultdict(list)

    def _prune(self, key: tuple[str, str], now: float) -> list[float]:
        """Drop old attempts outside the window."""
        cutoff = now - self.window_seconds
        attempts = [timestamp for timestamp in self._attempts[key] if timestamp > cutoff]
        self._attempts[key] = attempts
        return attempts

    def check_allowed(self, ip: str, email: str) -> bool:
        """Return True if another login attempt is allowed."""
        now = time.time()
        attempts = self._prune((ip, email), now)
        return len(attempts) < self.max_attempts

    def record_failure(self, ip: str, email: str) -> None:
        """Record a failed login attempt."""
        now = time.time()
        attempts = self._prune((ip, email), now)
        attempts.append(now)
        self._attempts[(ip, email)] = attempts

    def reset(self, ip: str, email: str) -> None:
        """Clear failed attempts after a successful login."""
        self._attempts.pop((ip, email), None)
