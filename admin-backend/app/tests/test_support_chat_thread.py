from __future__ import annotations


def test_user_send_then_poll_sees_own_message(client, user_headers):
    resp = client.post("/api/v1/support/chat", headers=user_headers, json={"message": "hello, need help"})
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    session_id = data["sessionId"]
    assert session_id is not None
    assert [m["sender"] for m in data["messages"]] == ["user"]
    assert data["messages"][0]["text"] == "hello, need help"

    poll = client.get("/api/v1/support/chat", headers=user_headers, params={"sessionId": session_id})
    assert poll.status_code == 200, poll.text
    assert [m["sender"] for m in poll.json()["data"]["messages"]] == ["user"]


def test_admin_reply_is_visible_to_the_user_on_next_poll(client, auth_headers, user_headers):
    """This is the exact bug being fixed: an admin's reply must show up the next
    time the app asks for the thread, not just be written to the database."""
    send = client.post("/api/v1/support/chat", headers=user_headers, json={"message": "otp not arriving"})
    session_id = send.json()["data"]["sessionId"]

    queries = client.get("/admin/queries?limit=10", headers=auth_headers).json()["items"]
    query_id = next(q["id"] for q in queries if q["id"] == int(session_id))

    reply = client.post(f"/admin/queries/{query_id}/reply", headers=auth_headers, json={"message": "please check spam folder"})
    assert reply.status_code == 200, reply.text

    poll = client.get("/api/v1/support/chat", headers=user_headers, params={"sessionId": session_id})
    assert poll.status_code == 200, poll.text
    messages = poll.json()["data"]["messages"]
    assert [m["sender"] for m in messages] == ["user", "admin"]
    assert messages[1]["text"] == "please check spam folder"


def test_second_user_message_still_shows_admins_earlier_reply(client, auth_headers, user_headers):
    send = client.post("/api/v1/support/chat", headers=user_headers, json={"message": "issue one"})
    session_id = send.json()["data"]["sessionId"]
    client.post(f"/admin/queries/{session_id}/reply", headers=auth_headers, json={"message": "working on it"})

    second = client.post("/api/v1/support/chat", headers=user_headers, json={"message": "thanks", "sessionId": session_id})
    assert second.status_code == 200, second.text
    senders = [m["sender"] for m in second.json()["data"]["messages"]]
    assert senders == ["user", "admin", "user"]


def test_poll_without_session_id_returns_most_recent_thread(client, user_headers):
    client.post("/api/v1/support/chat", headers=user_headers, json={"message": "first ticket"})
    resp = client.get("/api/v1/support/chat", headers=user_headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["messages"][0]["text"] == "first ticket"


def test_poll_with_no_thread_at_all_returns_empty(client, user_headers):
    resp = client.get("/api/v1/support/chat", headers=user_headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"] == {"sessionId": None, "status": None, "messages": []}
