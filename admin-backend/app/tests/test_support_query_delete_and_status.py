from __future__ import annotations


def test_admin_can_set_status_directly_without_replying(client, auth_headers, user_headers):
    send = client.post("/api/v1/support/chat", headers=user_headers, json={"message": "need help"})
    query_id = int(send.json()["data"]["sessionId"])

    resp = client.patch(f"/admin/queries/{query_id}/status", headers=auth_headers, json={"status": "Resolved"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "Resolved"

    listed = client.get("/admin/queries?limit=10", headers=auth_headers).json()["items"]
    assert next(q for q in listed if q["id"] == query_id)["status"] == "Resolved"


def test_status_update_rejects_unknown_value(client, auth_headers, user_headers):
    send = client.post("/api/v1/support/chat", headers=user_headers, json={"message": "need help"})
    query_id = send.json()["data"]["sessionId"]

    resp = client.patch(f"/admin/queries/{query_id}/status", headers=auth_headers, json={"status": "Closed"})
    assert resp.status_code == 422


def test_status_update_on_missing_query_is_404(client, auth_headers):
    resp = client.patch("/admin/queries/999999/status", headers=auth_headers, json={"status": "Open"})
    assert resp.status_code == 404


def test_admin_can_delete_a_query_and_its_messages(client, auth_headers, user_headers):
    send = client.post("/api/v1/support/chat", headers=user_headers, json={"message": "need help"})
    query_id = int(send.json()["data"]["sessionId"])
    client.post(f"/admin/queries/{query_id}/reply", headers=auth_headers, json={"message": "on it"})

    resp = client.delete(f"/admin/queries/{query_id}", headers=auth_headers)
    assert resp.status_code == 204

    listed = client.get("/admin/queries?limit=50", headers=auth_headers).json()["items"]
    assert query_id not in [q["id"] for q in listed]

    # The user's own poll must not resurrect or error on the deleted thread.
    poll = client.get("/api/v1/support/chat", headers=user_headers, params={"sessionId": query_id})
    assert poll.status_code == 200, poll.text
    assert poll.json()["data"]["messages"] == []


def test_delete_missing_query_is_404(client, auth_headers):
    resp = client.delete("/admin/queries/999999", headers=auth_headers)
    assert resp.status_code == 404
