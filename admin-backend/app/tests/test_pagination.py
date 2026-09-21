from __future__ import annotations


def test_users_pagination_slice_and_total(client, auth_headers):
    for i in range(5):
        client.post("/admin/users", headers=auth_headers, json={"name": f"User {i}", "phone": f"91000000{i:02d}"})

    all_users = client.get("/admin/users?limit=50", headers=auth_headers).json()
    assert all_users["total"] == 6  # 1 seeded + 5 created

    page = client.get("/admin/users?limit=2&offset=2", headers=auth_headers).json()
    assert page["limit"] == 2
    assert page["offset"] == 2
    assert len(page["items"]) == 2
    assert page["total"] == 6

    full_ordered_ids = [s["id"] for s in all_users["items"]]
    page_ids = [s["id"] for s in page["items"]]
    assert page_ids == full_ordered_ids[2:4]


def test_pagination_limit_bounds_enforced(client, auth_headers):
    resp = client.get("/admin/users?limit=0", headers=auth_headers)
    assert resp.status_code == 422

    resp = client.get("/admin/users?limit=500", headers=auth_headers)
    assert resp.status_code == 422
