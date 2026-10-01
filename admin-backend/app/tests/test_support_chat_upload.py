from __future__ import annotations

import re

from app.core import ratelimit

_UUID_RE = re.compile(r"^/api/v1/support/chat/attachments/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")

_TINY_JPEG = bytes.fromhex("ffd8ffe000104a46494600010100000100010000ffd9")  # minimal valid-shaped JPEG bytes


def test_upload_image_then_fetch_it_back(client, user_headers):
    resp = client.post(
        "/api/v1/support/chat/upload", headers=user_headers,
        files={"file": ("photo.jpg", _TINY_JPEG, "image/jpeg")},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["attachmentType"] == "image"
    assert _UUID_RE.match(data["attachmentUrl"])

    fetch = client.get(data["attachmentUrl"])  # no auth header at all
    assert fetch.status_code == 200
    assert fetch.headers["content-type"] == "image/jpeg"
    assert fetch.content == _TINY_JPEG


def test_upload_audio_is_typed_correctly(client, user_headers):
    resp = client.post(
        "/api/v1/support/chat/upload", headers=user_headers,
        files={"file": ("note.m4a", b"fake-audio-bytes", "audio/mp4")},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["attachmentType"] == "audio"


def test_unsupported_file_type_rejected(client, user_headers):
    resp = client.post(
        "/api/v1/support/chat/upload", headers=user_headers,
        files={"file": ("shell.sh", b"#!/bin/sh\necho hi", "application/x-sh")},
    )
    assert resp.status_code == 400


def test_svg_is_rejected_even_though_it_starts_with_image(client, user_headers):
    """image/svg+xml can carry an embedded <script> -- explicitly not on the
    allowlist, unlike a naive "image/*" prefix check would allow."""
    resp = client.post(
        "/api/v1/support/chat/upload", headers=user_headers,
        files={"file": ("evil.svg", b"<svg onload='alert(1)'></svg>", "image/svg+xml")},
    )
    assert resp.status_code == 400


def test_empty_file_rejected(client, user_headers):
    resp = client.post(
        "/api/v1/support/chat/upload", headers=user_headers,
        files={"file": ("empty.jpg", b"", "image/jpeg")},
    )
    assert resp.status_code == 400


def test_oversized_file_rejected(client, user_headers):
    big = b"\x00" * (8 * 1024 * 1024 + 1)
    resp = client.post(
        "/api/v1/support/chat/upload", headers=user_headers,
        files={"file": ("big.jpg", big, "image/jpeg")},
    )
    assert resp.status_code == 400


def test_upload_requires_authentication(client):
    resp = client.post(
        "/api/v1/support/chat/upload",
        files={"file": ("photo.jpg", _TINY_JPEG, "image/jpeg")},
    )
    assert resp.status_code == 401


def test_fetching_a_nonexistent_attachment_404s(client):
    resp = client.get("/api/v1/support/chat/attachments/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


def test_uploaded_attachment_can_be_sent_as_a_chat_message(client, auth_headers, user_headers):
    upload = client.post(
        "/api/v1/support/chat/upload", headers=user_headers,
        files={"file": ("photo.jpg", _TINY_JPEG, "image/jpeg")},
    )
    attachment_url = upload.json()["data"]["attachmentUrl"]

    send = client.post(
        "/api/v1/support/chat", headers=user_headers,
        json={"attachmentUrl": attachment_url, "attachmentType": "image"},
    )
    assert send.status_code == 200, send.text
    message = send.json()["data"]["messages"][0]
    assert message["attachmentUrl"] == attachment_url
    assert message["attachmentType"] == "image"

    session_id = send.json()["data"]["sessionId"]
    queries = client.get("/admin/queries?limit=10", headers=auth_headers).json()["items"]
    admin_view = next(q for q in queries if q["id"] == int(session_id))
    assert admin_view["messages"][0]["attachmentUrl"] == attachment_url


def test_upload_rate_limit_kicks_in(client, user_headers):
    for _ in range(ratelimit.SUPPORT_UPLOAD_MAX_PER_USER_WINDOW):
        resp = client.post(
            "/api/v1/support/chat/upload", headers=user_headers,
            files={"file": ("photo.jpg", _TINY_JPEG, "image/jpeg")},
        )
        assert resp.status_code == 200

    resp = client.post(
        "/api/v1/support/chat/upload", headers=user_headers,
        files={"file": ("photo.jpg", _TINY_JPEG, "image/jpeg")},
    )
    assert resp.status_code == 429
    assert "Retry-After" in resp.headers
