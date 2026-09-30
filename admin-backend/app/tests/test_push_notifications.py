from __future__ import annotations

from unittest.mock import patch

from app.core.errors import AppError
from app.services import firebase_service
from app.tests.conftest import TestingSessionLocal
from app.models.user import User


def _user_id(client, auth_headers) -> int:
    return next(u["id"] for u in client.get("/admin/users?limit=50", headers=auth_headers).json()["items"] if u["phone"] == "9000000000")


def test_login_saves_fcm_token(client, user_headers):
    resp = client.post("/api/v1/auth/login", json={"phone": "9000000000", "password": "user12345", "fcmToken": "device-token-abc"})
    assert resp.status_code == 200, resp.text

    db = TestingSessionLocal()
    user = db.query(User).filter(User.phone == "9000000000").first()
    assert user.fcm_token == "device-token-abc"
    db.close()


def test_login_without_fcm_token_keeps_previous_one(client):
    client.post("/api/v1/auth/login", json={"phone": "9000000000", "password": "user12345", "fcmToken": "keep-me"})
    client.post("/api/v1/auth/login", json={"phone": "9000000000", "password": "user12345"})

    db = TestingSessionLocal()
    user = db.query(User).filter(User.phone == "9000000000").first()
    assert user.fcm_token == "keep-me"
    db.close()


def test_send_push_fails_loudly_when_unconfigured():
    firebase_service.reset_for_tests()
    try:
        try:
            firebase_service.send_push("some-token", "Title", "Body")
            assert False, "expected AppError"
        except AppError as exc:
            assert exc.code == "FIREBASE_NOT_CONFIGURED"
    finally:
        firebase_service.reset_for_tests()


def test_notify_rejects_user_with_no_fcm_token(client, auth_headers, user_headers):
    uid = _user_id(client, auth_headers)
    resp = client.post(f"/admin/users/{uid}/notify", headers=auth_headers, json={"title": "Hi", "body": "There"})
    assert resp.status_code == 400
    assert resp.json()["error"] == "NO_FCM_TOKEN"


def test_notify_sends_push_via_firebase(client, auth_headers, user_headers):
    uid = _user_id(client, auth_headers)
    client.post("/api/v1/auth/login", json={"phone": "9000000000", "password": "user12345", "fcmToken": "device-xyz"})

    with patch("app.routers.admin.users.firebase_service.send_push", return_value="projects/x/messages/123") as mock_send:
        resp = client.post(f"/admin/users/{uid}/notify", headers=auth_headers, json={"title": "Result published", "body": "Check your bids"})

    assert resp.status_code == 200, resp.text
    assert resp.json()["firebaseMessageId"] == "projects/x/messages/123"
    mock_send.assert_called_once_with("device-xyz", "Result published", "Check your bids")

    audit = client.get("/admin/audit-logs?limit=1", headers=auth_headers).json()["items"][0]
    assert audit["action"] == "user_notified"
