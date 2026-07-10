from app.services.rate_limiter import LoginRateLimiter


def test_rate_limiter_blocks_after_max_failures():
    limiter = LoginRateLimiter(max_attempts=3, window_seconds=60)

    assert limiter.check_allowed("127.0.0.1", "user@example.com") is True
    limiter.record_failure("127.0.0.1", "user@example.com")
    limiter.record_failure("127.0.0.1", "user@example.com")
    limiter.record_failure("127.0.0.1", "user@example.com")

    assert limiter.check_allowed("127.0.0.1", "user@example.com") is False


def test_rate_limiter_reset_clears_failures():
    limiter = LoginRateLimiter(max_attempts=2, window_seconds=60)

    limiter.record_failure("127.0.0.1", "user@example.com")
    limiter.record_failure("127.0.0.1", "user@example.com")
    assert limiter.check_allowed("127.0.0.1", "user@example.com") is False

    limiter.reset("127.0.0.1", "user@example.com")
    assert limiter.check_allowed("127.0.0.1", "user@example.com") is True


def test_rate_limiter_tracks_ip_and_email_separately():
    limiter = LoginRateLimiter(max_attempts=1, window_seconds=60)

    limiter.record_failure("127.0.0.1", "user@example.com")
    assert limiter.check_allowed("127.0.0.1", "user@example.com") is False
    assert limiter.check_allowed("127.0.0.1", "other@example.com") is True
    assert limiter.check_allowed("10.0.0.1", "user@example.com") is True
