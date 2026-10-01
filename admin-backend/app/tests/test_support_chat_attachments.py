from __future__ import annotations

import re


_TIME_RE = re.compile(r"^(0[1-9]|1[0-2]):[0-5]\d (AM|PM)$")


def test_image_only_message_with_no_text_succeeds(client, user_headers):
    resp = client.post(
        "/api/v1/support/chat", headers=user_headers,
        json={"attachmentUrl": "https://firebasestorage.googleapis.com/x/photo.jpg", "attachmentType": "image"},
    )
    assert resp.status_code == 200, resp.text
    messages = resp.json()["data"]["messages"]
    assert len(messages) == 1
    assert messages[0]["text"] is None
    assert messages[0]["attachmentUrl"] == "https://firebasestorage.googleapis.com/x/photo.jpg"
    assert messages[0]["attachmentType"] == "image"


def test_voice_message_with_caption_keeps_both(client, user_headers):
    resp = client.post(
        "/api/v1/support/chat", headers=user_headers,
        json={"message": "this is what happened", "attachmentUrl": "https://firebasestorage.googleapis.com/x/note.m4a", "attachmentType": "audio"},
    )
    assert resp.status_code == 200, resp.text
    message = resp.json()["data"]["messages"][0]
    assert message["text"] == "this is what happened"
    assert message["attachmentType"] == "audio"


def test_empty_message_with_no_attachment_rejected(client, user_headers):
    resp = client.post("/api/v1/support/chat", headers=user_headers, json={})
    assert resp.status_code == 422


def test_attachment_url_without_type_rejected(client, user_headers):
    resp = client.post(
        "/api/v1/support/chat", headers=user_headers,
        json={"attachmentUrl": "https://firebasestorage.googleapis.com/x/photo.jpg"},
    )
    assert resp.status_code == 422


def test_admin_can_reply_with_an_attachment(client, auth_headers, user_headers):
    send = client.post("/api/v1/support/chat", headers=user_headers, json={"message": "how do I withdraw"})
    session_id = send.json()["data"]["sessionId"]

    reply = client.post(
        f"/admin/queries/{session_id}/reply", headers=auth_headers,
        json={"attachmentUrl": "https://firebasestorage.googleapis.com/x/steps.png", "attachmentType": "image"},
    )
    assert reply.status_code == 200, reply.text

    poll = client.get("/api/v1/support/chat", headers=user_headers, params={"sessionId": session_id})
    messages = poll.json()["data"]["messages"]
    assert messages[1]["sender"] == "admin"
    assert messages[1]["attachmentUrl"] == "https://firebasestorage.googleapis.com/x/steps.png"
    assert messages[1]["attachmentType"] == "image"


def test_admin_reply_with_neither_text_nor_attachment_rejected(client, auth_headers, user_headers):
    send = client.post("/api/v1/support/chat", headers=user_headers, json={"message": "hello"})
    session_id = send.json()["data"]["sessionId"]
    reply = client.post(f"/admin/queries/{session_id}/reply", headers=auth_headers, json={})
    assert reply.status_code == 422


def test_message_time_is_valid_12_hour_clock(client, user_headers):
    """Regression: time was previously built with `%H:%M %p` -- 24-hour hour
    plus an AM/PM suffix, producing nonsense like "17:10 PM"."""
    resp = client.post("/api/v1/support/chat", headers=user_headers, json={"message": "hi"})
    time_str = resp.json()["data"]["messages"][0]["time"]
    assert _TIME_RE.match(time_str), f"not a valid 12-hour clock string: {time_str!r}"


def test_admin_reply_time_is_also_a_valid_12_hour_clock(client, auth_headers, user_headers):
    send = client.post("/api/v1/support/chat", headers=user_headers, json={"message": "hi"})
    session_id = send.json()["data"]["sessionId"]
    reply = client.post(f"/admin/queries/{session_id}/reply", headers=auth_headers, json={"message": "hello back"})
    messages = reply.json()["messages"]
    assert _TIME_RE.match(messages[-1]["time"]), f"not a valid 12-hour clock string: {messages[-1]['time']!r}"


def test_history_shows_friendly_preview_for_attachment_only_last_message(client, user_headers):
    client.post(
        "/api/v1/support/chat", headers=user_headers,
        json={"attachmentUrl": "https://firebasestorage.googleapis.com/x/note.m4a", "attachmentType": "audio"},
    )
    history = client.get("/api/v1/support/chat/history", headers=user_headers)
    assert history.json()["data"]["chats"][0]["lastMessage"] == "🎤 Voice message"


def test_admin_queries_list_surfaces_attachment_fields(client, auth_headers, user_headers):
    client.post(
        "/api/v1/support/chat", headers=user_headers,
        json={"attachmentUrl": "https://firebasestorage.googleapis.com/x/photo.jpg", "attachmentType": "image"},
    )
    queries = client.get("/admin/queries?limit=10", headers=auth_headers).json()["items"]
    latest = queries[0]
    assert latest["messages"][0]["attachmentUrl"] == "https://firebasestorage.googleapis.com/x/photo.jpg"
    assert latest["messages"][0]["attachmentType"] == "image"
