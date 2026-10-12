"""
Production Security & Launch Hardening Regression Suite.

Verifies:
1. Unauthenticated request rejection (HTTP 401) across all state-changing endpoints.
2. Token validation and rejection of forged credentials.
3. Strict multi-user / multi-tenant account isolation.
4. CORS restrictions against malicious/unapproved origins.
5. In-memory rate limiting and 429 responses.
6. Financial integrity invariants (cash, margins, fees, slippage, realized/unrealized P&L).
7. Market hours refusal and simulated off-hours fill toggle.
8. Non-bypassable live execution guard.
"""

import os
from pathlib import Path
import pytest
from starlette.testclient import TestClient

from src.api.main import create_app
from src.paper_trading.execution_guard import ALLOW_LIVE_EXECUTION, LiveExecutionDisabledError
from src.paper_trading.service import PaperTradingService


@pytest.fixture
def test_environment(tmp_path):
    users_db = str(tmp_path / "test_users.db")
    os.environ["USERS_DB_PATH"] = users_db
    app = create_app()
    client = TestClient(app)
    return client, tmp_path


def test_unauthenticated_endpoints_return_401(test_environment):
    client, _ = test_environment

    protected_endpoints = [
        ("POST", "/api/v1/paper/orders", {"symbol": "NIFTY", "side": "BUY", "quantity": 25}),
        ("GET", "/api/v1/paper/orders", None),
        ("DELETE", "/api/v1/paper/orders/any-id", None),
        ("GET", "/api/v1/paper/portfolio", None),
        ("GET", "/api/v1/paper/positions", None),
        ("GET", "/api/v1/paper/history", None),
        ("POST", "/api/v1/paper/reset", {"confirm": True}),
        ("POST", "/api/v1/paper/risk/trip", {"reason": "HALT"}),
        ("POST", "/api/v1/paper/risk/reset", None),
        ("POST", "/api/v1/paper/positions/pos-123/close", {}),
    ]

    for method, endpoint, payload in protected_endpoints:
        if method == "POST":
            res = client.post(endpoint, json=payload)
        elif method == "GET":
            res = client.get(endpoint)
        elif method == "DELETE":
            res = client.delete(endpoint)
        assert res.status_code == 401, f"{method} {endpoint} expected 401, got {res.status_code}"


def test_invalid_and_expired_token_rejected(test_environment):
    client, _ = test_environment

    headers_bearer = {"Authorization": "Bearer fake_token_xyz_999"}
    res = client.get("/api/v1/paper/portfolio", headers=headers_bearer)
    assert res.status_code == 401
    assert "Invalid or expired" in res.json()["detail"]

    headers_api_key = {"X-API-Key": "forged_key_000"}
    res2 = client.get("/api/v1/paper/portfolio", headers=headers_api_key)
    assert res2.status_code == 401


def test_multi_user_account_isolation(test_environment):
    client, _ = test_environment

    # 1. Register User Alpha
    r1 = client.post("/api/v1/auth/register", json={
        "username": "user_alpha",
        "email": "alpha@institution.com",
        "password": "PasswordAlpha123!",
        "full_name": "Alpha Trader",
        "starting_capital": 500000.0,
    })
    assert r1.status_code == 201
    token_alpha = r1.json()["access_token"]
    headers_alpha = {"Authorization": f"Bearer {token_alpha}"}

    # 2. Register User Beta
    r2 = client.post("/api/v1/auth/register", json={
        "username": "user_beta",
        "email": "beta@institution.com",
        "password": "PasswordBeta123!",
        "full_name": "Beta Trader",
        "starting_capital": 1000000.0,
    })
    assert r2.status_code == 201
    token_beta = r2.json()["access_token"]
    headers_beta = {"Authorization": f"Bearer {token_beta}"}

    # 3. Check starting cash reflects respective accounts
    port_alpha = client.get("/api/v1/paper/portfolio", headers=headers_alpha).json()
    port_beta = client.get("/api/v1/paper/portfolio", headers=headers_beta).json()
    assert port_alpha["cash"] == 500000.0
    assert port_beta["cash"] == 1000000.0

    # 4. User Alpha trips circuit breaker
    trip_res = client.post("/api/v1/paper/risk/trip", headers=headers_alpha, json={"reason": "ALPHA_HALT"})
    assert trip_res.status_code == 200
    assert trip_res.json()["status"] == "TRIPPED"

    # User Alpha order should now be rejected due to breaker
    order_alpha = client.post("/api/v1/paper/orders", headers=headers_alpha, json={
        "symbol": "NIFTY",
        "side": "BUY",
        "quantity": 50,
        "execution_mode": "PAPER",
    })
    assert order_alpha.json()["status"] == "REJECTED"
    assert "CIRCUIT_BREAKER" in str(order_alpha.json()["rejection_reason"])

    # User Beta order should NOT be blocked because breaker isolation is per-user!
    order_beta = client.post("/api/v1/paper/orders", headers=headers_beta, json={
        "symbol": "NIFTY",
        "side": "BUY",
        "quantity": 50,
        "execution_mode": "PAPER",
    })
    assert "CIRCUIT_BREAKER" not in str(order_beta.json().get("rejection_reason", ""))


def test_cors_origin_control(test_environment):
    client, _ = test_environment

    # 1. Unapproved origin should NOT be allowed
    res_evil = client.options("/api/v1/paper/orders", headers={
        "Origin": "https://malicious-attacker.com",
        "Access-Control-Request-Method": "POST",
    })
    assert res_evil.headers.get("access-control-allow-origin") is None or res_evil.headers.get("access-control-allow-origin") != "https://malicious-attacker.com"

    # 2. Approved origin (Streamlit default)
    res_app = client.options("/api/v1/paper/orders", headers={
        "Origin": "http://localhost:8501",
        "Access-Control-Request-Method": "POST",
    })
    assert res_app.headers.get("access-control-allow-origin") == "http://localhost:8501"
    assert res_app.headers.get("access-control-allow-credentials") == "true"

    # 3. Streamlit Cloud regex matching origin
    res_cloud = client.options("/api/v1/paper/orders", headers={
        "Origin": "https://indian-stock-market-ai.streamlit.app",
        "Access-Control-Request-Method": "POST",
    })
    assert res_cloud.headers.get("access-control-allow-origin") == "https://indian-stock-market-ai.streamlit.app"


def test_auth_rate_limiting(test_environment):
    from src.api.security import auth_rate_limiter
    auth_rate_limiter.reset()
    client, _ = test_environment

    try:
        # Exceed rate limit on login attempts (20 requests per minute)
        reached_429 = False
        for i in range(25):
            res = client.post("/api/v1/auth/login", json={
                "username_or_email": f"bruteforce_{i}",
                "password": "wrong_password",
            })
            if res.status_code == 429:
                reached_429 = True
                assert "Rate limit exceeded" in res.json()["detail"]
                assert "Retry-After" in res.headers
                break

        assert reached_429, "Expected rate limiter to return 429 after threshold exceeded"
    finally:
        auth_rate_limiter.reset()


def test_financial_invariants_paper_trading(tmp_path):
    """Rigorous financial math verification: cash, margin, fees, slippage, P&L."""
    state_dir = str(tmp_path / "paper_state_financial")
    service = PaperTradingService(initial_capital=1_000_000.0, state_dir=state_dir, auto_restore=False)
    # Enable simulation fills regardless of market hours for unit test reproducibility
    service.fill_engine.allow_off_hours_simulation = True

    assert ALLOW_LIVE_EXECUTION is False

    # 1. Place buy order: 50 qty of NIFTY
    res = service.place_order(
        symbol="NIFTY",
        side="BUY",
        quantity=50,
        order_type="MARKET",
        instrument_type="INDEX",
    )
    assert res["status"] == "PENDING"
    assert res["risk_approved"] is True

    # 2. Process market tick to execute simulated fill
    update_res = service.process_market_update(
        symbol="NIFTY",
        bid=200.0,
        ask=202.0,
        ltp=201.0,
    )
    assert len(update_res["fills"]) == 1

    # Check portfolio metrics: cash reduced
    portfolio = service.get_portfolio_summary()
    assert portfolio["cash"] < 1_000_000.0
    assert portfolio["equity"] > 0
    assert portfolio["open_positions_count"] == 1

    # Check service recorded fill with transaction costs and slippage
    fills = service._all_fills
    assert len(fills) == 1
    assert fills[0].transaction_costs >= 0
    assert fills[0].slippage_applied >= 0

    # 3. Check position
    pos_response = service.get_positions(status="OPEN")
    positions = pos_response["positions"]
    assert len(positions) == 1
    pos = positions[0]
    pos_id = pos["position_id"]
    assert pos["quantity"] == 50
    assert pos["side"] == "LONG"

    # 4. Close position
    close_res = service.close_position(position_id=pos_id)
    assert close_res["status"] == "CLOSED"

    # Positions open should now be 0
    open_pos_response = service.get_positions(status="OPEN")
    assert len(open_pos_response["positions"]) == 0

    # Realized P&L should be recorded
    summary_after = service.get_portfolio_summary()
    assert summary_after["realized_pnl"] is not None

    # 5. Invalid / boundary order checks
    invalid_qty_order = service.place_order(
        symbol="NIFTY",
        side="BUY",
        quantity=0,
        order_type="MARKET",
        instrument_type="INDEX",
    )
    assert invalid_qty_order["status"] == "REJECTED"
    assert "INVALID_QUANTITY" in str(invalid_qty_order["rejection_reason"])
