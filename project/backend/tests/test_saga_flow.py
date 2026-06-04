"""
E2E integration test for the full ticket-purchase Saga flow.

Runs against a live stack (docker-compose up) via the API Gateway.
"""
from __future__ import annotations

import asyncio
import uuid

import httpx
import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

POLL_INTERVAL_S = 2
POLL_MAX_ATTEMPTS = 15
TERMINAL_STATUSES = {"completed", "payment_failed"}


def _random_email() -> str:
    return f"test_{uuid.uuid4().hex[:8]}@example.com"


async def _register_and_login(gateway: httpx.AsyncClient) -> tuple[dict[str, str], str]:
    email = _random_email()
    password = "StrongPass123!"

    resp = await gateway.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": "E2E Tester"},
    )
    assert resp.status_code == 201, f"Register failed: {resp.text}"

    resp = await gateway.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    payload = resp.json()
    return {"Authorization": f"Bearer {payload['access_token']}"}, payload["user_id"]


async def _create_session_with_seats(gateway: httpx.AsyncClient, admin_headers: dict[str, str]) -> str:
    resp = await gateway.post(
        "/api/admin/categories",
        json={
            "name_ru": f"Кат_{uuid.uuid4().hex[:6]}",
            "name_en": f"Cat_{uuid.uuid4().hex[:6]}",
            "name_kz": f"Кат_{uuid.uuid4().hex[:6]}",
        },
        headers=admin_headers,
    )
    assert resp.status_code == 200, f"Create category failed: {resp.text}"
    category_id = resp.json()["id"]

    resp = await gateway.post(
        "/api/admin/cities",
        json={
            "name_ru": f"Город_{uuid.uuid4().hex[:6]}",
            "name_en": f"City_{uuid.uuid4().hex[:6]}",
            "name_kz": f"Қала_{uuid.uuid4().hex[:6]}",
        },
        headers=admin_headers,
    )
    assert resp.status_code == 200, f"Create city failed: {resp.text}"
    city_id = resp.json()["id"]

    resp = await gateway.post(
        "/api/admin/events",
        json={
            "title": f"E2E Concert {uuid.uuid4().hex[:6]}",
            "description": "Auto-generated for E2E test",
            "category_id": category_id,
            "city_id": city_id,
        },
        headers=admin_headers,
    )
    assert resp.status_code == 200, f"Create event failed: {resp.text}"
    event_id = resp.json()["id"]

    resp = await gateway.post(
        f"/api/admin/events/{event_id}/sessions",
        json={
            "start_time": "2030-01-01T12:00:00Z",
            "hall_name": "E2E Hall",
            "price": 7000,
        },
        headers=admin_headers,
    )
    assert resp.status_code == 200, f"Create session failed: {resp.text}"
    session_id = resp.json()["id"]

    resp = await gateway.post(
        f"/api/admin/seats/generate/{session_id}",
        json={"rows": 2, "seats_per_row": 5},
        headers=admin_headers,
    )
    assert resp.status_code == 200, f"Generate seats failed: {resp.text}"
    assert resp.json()["total_created"] == 10
    return session_id


async def _get_free_seat_id(gateway: httpx.AsyncClient, session_id: str) -> str:
    resp = await gateway.get(f"/api/seats/{session_id}")
    assert resp.status_code == 200, f"Get seats failed: {resp.text}"
    free_seats = [s for s in resp.json() if s["status"] == "free"]
    assert free_seats, "No free seats available"
    return free_seats[0]["id"]


async def _start_buy(gateway: httpx.AsyncClient, user_headers: dict[str, str], user_id: str, seat_id: str) -> str:
    resp = await gateway.post(
        "/api/buy",
        json={"seat_ids": [seat_id]},
        headers={**user_headers, "X-User-Id": str(user_id)},
    )
    assert resp.status_code in (200, 202), f"Buy failed: {resp.text}"
    body = resp.json()
    assert body["status"] == "PROCESSING"
    return body["booking_id"]


async def _poll_status(
    gateway: httpx.AsyncClient,
    user_headers: dict[str, str],
    booking_id: str,
) -> dict:
    status_body: dict = {}
    for attempt in range(1, POLL_MAX_ATTEMPTS + 1):
        await asyncio.sleep(POLL_INTERVAL_S)
        resp = await gateway.get(f"/api/status/{booking_id}", headers=user_headers)
        assert resp.status_code == 200, f"Status poll failed (attempt {attempt}): {resp.text}"
        status_body = resp.json()
        if status_body.get("status") in TERMINAL_STATUSES:
            return status_body
    raise AssertionError(
        f"Saga did not reach terminal state within {POLL_MAX_ATTEMPTS * POLL_INTERVAL_S}s. "
        f"Last status: {status_body.get('status')}"
    )


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_full_ticket_purchase_saga(
    gateway: httpx.AsyncClient,
    admin_headers: dict[str, str],
):
    user_headers, user_id = await _register_and_login(gateway)
    session_id = await _create_session_with_seats(gateway, admin_headers)
    seat_id = await _get_free_seat_id(gateway, session_id)
    booking_id = await _start_buy(gateway, user_headers, user_id, seat_id)
    status_body = await _poll_status(gateway, user_headers, booking_id)
    final_status = status_body["status"]

    if final_status == "completed":
        ticket_url = status_body.get("ticket_url") or ""
        assert ticket_url, "completed saga must have ticket_url"
        assert "/tickets/" in ticket_url and ".pdf" in ticket_url
        assert str(booking_id) in ticket_url
    else:
        assert status_body.get("error_reason"), "payment_failed saga must have error_reason"


@pytest.mark.asyncio
async def test_payment_failed_branch_eventually_observed(
    gateway: httpx.AsyncClient,
    admin_headers: dict[str, str],
):
    # Payment outcome is randomized in payment_service; run bounded retries.
    user_headers, user_id = await _register_and_login(gateway)

    attempts = 8
    for _ in range(attempts):
        session_id = await _create_session_with_seats(gateway, admin_headers)
        seat_id = await _get_free_seat_id(gateway, session_id)
        booking_id = await _start_buy(gateway, user_headers, user_id, seat_id)
        status_body = await _poll_status(gateway, user_headers, booking_id)

        if status_body["status"] == "payment_failed":
            assert status_body.get("error_reason"), "payment_failed saga must provide error_reason"
            return

    pytest.skip(f"payment_failed was not observed in {attempts} attempts due to randomized bank simulator")


@pytest.mark.asyncio
async def test_repeat_buy_same_seat_is_rejected_or_compensated(
    gateway: httpx.AsyncClient,
    admin_headers: dict[str, str],
):
    user_headers, user_id = await _register_and_login(gateway)
    session_id = await _create_session_with_seats(gateway, admin_headers)
    seat_id = await _get_free_seat_id(gateway, session_id)

    first_booking = await _start_buy(gateway, user_headers, user_id, seat_id)
    first_status = await _poll_status(gateway, user_headers, first_booking)
    assert first_status["status"] in TERMINAL_STATUSES

    second_booking = await _start_buy(gateway, user_headers, user_id, seat_id)
    second_status = await _poll_status(gateway, user_headers, second_booking)

    # Repeated buy on same seat should never produce a second successful completion.
    if first_status["status"] == "completed":
        assert second_status["status"] != "completed", (
            "Second buy for the same seat unexpectedly completed; expected rejection/compensation."
        )
