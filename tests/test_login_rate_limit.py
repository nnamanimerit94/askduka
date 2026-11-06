from backend.app.login_rate_limit import LoginRateLimiter


def test_limiter_blocks_sixth_attempt_within_window():
    limiter = LoginRateLimiter(max_attempts=5, window_seconds=300)
    assert all(limiter.allow("192.0.2.1", now=100 + i) for i in range(5))
    assert not limiter.allow("192.0.2.1", now=105)
    assert limiter.allow("192.0.2.2", now=105)


def test_limiter_resets_after_window():
    limiter = LoginRateLimiter(max_attempts=1, window_seconds=30)
    assert limiter.allow("client", now=0)
    assert not limiter.allow("client", now=1)
    assert limiter.allow("client", now=31)
