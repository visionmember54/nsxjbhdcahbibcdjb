from __future__ import annotations

from app.core import ratelimit


def _second_user_headers(client, auth_headers):
    resp = client.post(
        "/admin/users", headers=auth_headers,
        json={"name": "Second User", "phone": "9111111111", "email": "second@example.com", "password": "seconduser123"},
    )
    assert resp.status_code == 201, resp.text
    token = client.post("/auth/login", json={"phone": "9111111111", "password": "seconduser123"}).json()["token"]
    return {"Authorization": f"Bearer {token}"}


def test_user_can_resolve_their_own_chat(client, user_headers):
    send = client.post("/api/v1/support/chat", headers=user_headers, json={"message": "issue solved itself, nevermind"})
    session_id = send.json()["data"]["sessionId"]

    resolve = client.post("/api/v1/support/chat/resolve", headers=user_headers, json={"sessionId": session_id})
    assert resolve.status_code == 200, resolve.text
    assert resolve.json()["data"]["status"] == "Resolved"

    poll = client.get("/api/v1/support/chat", headers=user_headers, params={"sessionId": session_id})
    assert poll.json()["data"]["status"] == "Resolved"


def test_sending_after_resolve_starts_a_fresh_thread_not_reopening_the_old_one(client, user_headers):
    first = client.post("/api/v1/support/chat", headers=user_headers, json={"message": "first question"})
    first_id = first.json()["data"]["sessionId"]
    client.post("/api/v1/support/chat/resolve", headers=user_headers, json={"sessionId": first_id})

    second = client.post("/api/v1/support/chat", headers=user_headers, json={"message": "a new, unrelated question"})
    second_id = second.json()["data"]["sessionId"]

    assert second_id != first_id
    assert second.json()["data"]["messages"] == [m for m in second.json()["data"]["messages"] if m["text"] == "a new, unrelated question"]

    # The resolved thread is untouched and still fetchable directly by id.
    old = client.get("/api/v1/support/chat", headers=user_headers, params={"sessionId": first_id})
    assert old.json()["data"]["status"] == "Resolved"
    assert old.json()["data"]["messages"][0]["text"] == "first question"


def test_history_lists_both_resolved_and_active_chats_most_recent_first(client, user_headers):
    first = client.post("/api/v1/support/chat", headers=user_headers, json={"message": "old chat"})
    first_id = first.json()["data"]["sessionId"]
    client.post("/api/v1/support/chat/resolve", headers=user_headers, json={"sessionId": first_id})
    client.post("/api/v1/support/chat", headers=user_headers, json={"message": "new chat"})

    history = client.get("/api/v1/support/chat/history", headers=user_headers)
    assert history.status_code == 200, history.text
    chats = history.json()["data"]["chats"]
    assert len(chats) == 2
    assert chats[0]["lastMessage"] == "new chat"
    assert chats[0]["status"] == "Open"
    assert chats[1]["lastMessage"] == "old chat"
    assert chats[1]["status"] == "Resolved"


def test_user_cannot_read_another_users_chat(client, auth_headers, user_headers):
    mine = client.post("/api/v1/support/chat", headers=user_headers, json={"message": "private question"})
    session_id = mine.json()["data"]["sessionId"]

    other_headers = _second_user_headers(client, auth_headers)
    poll = client.get("/api/v1/support/chat", headers=other_headers, params={"sessionId": session_id})
    assert poll.status_code == 200, poll.text
    # Not their session -> falls back to "no thread of mine", never someone else's data.
    assert poll.json()["data"]["sessionId"] is None


def test_user_cannot_resolve_another_users_chat(client, auth_headers, user_headers):
    mine = client.post("/api/v1/support/chat", headers=user_headers, json={"message": "private question"})
    session_id = mine.json()["data"]["sessionId"]

    other_headers = _second_user_headers(client, auth_headers)
    resolve = client.post("/api/v1/support/chat/resolve", headers=other_headers, json={"sessionId": session_id})
    assert resolve.status_code == 404


def test_anonymous_request_is_rejected(client):
    resp = client.get("/api/v1/support/chat")
    assert resp.status_code == 401


def test_send_rate_limit_kicks_in_after_repeated_sends(client, user_headers):
    for _ in range(ratelimit.SUPPORT_CHAT_MAX_PER_USER_WINDOW):
        resp = client.post("/api/v1/support/chat", headers=user_headers, json={"message": "spam"})
        assert resp.status_code == 200

    resp = client.post("/api/v1/support/chat", headers=user_headers, json={"message": "one too many"})
    assert resp.status_code == 429
    assert "Retry-After" in resp.headers
