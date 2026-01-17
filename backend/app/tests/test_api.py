import pytest
from rest_framework.test import APIClient
from app.models import Member

@pytest.mark.django_db
def test_full_happy_path_and_completed_reject():
    Member.objects.create(member_number="12345678", name="山田 太郎", is_active=True)
    c = APIClient()

    r = c.post("/api/sessions", format="json")
    assert r.status_code in (200, 201)
    sid = r.data["session_id"]

    r = c.post(f"/api/sessions/{sid}/member-lookup", {"member_number": "12345678"}, format="json")
    assert r.status_code == 200
    assert r.data["state"] == "ASK_ORDER"

    r = c.post(f"/api/sessions/{sid}/order", {"order_number": "10020030", "quantity": 1}, format="json")
    assert r.status_code == 200
    assert r.data["state"] == "COMPLETED"

    # COMPLETED後は拒否(409)
    r = c.post(f"/api/sessions/{sid}/order", {"order_number": "10020030", "quantity": 1}, format="json")
    assert r.status_code == 409
    assert r.data["error"]["code"] == "ALREADY_COMPLETED"

@pytest.mark.django_db
def test_member_lookup_not_found():
    c = APIClient()
    r = c.post("/api/sessions", format="json")
    sid = r.data["session_id"]

    r = c.post(f"/api/sessions/{sid}/member-lookup", {"member_number": "99999999"}, format="json")
    assert r.status_code == 400
    assert r.data["error"]["code"] == "MEMBER_NOT_FOUND"
    assert r.data["state"] == "ASK_MEMBER"

@pytest.mark.django_db
def test_order_validation_error():
    Member.objects.create(member_number="12345678", name="山田 太郎", is_active=True)
    c = APIClient()
    sid = c.post("/api/sessions", format="json").data["session_id"]
    c.post(f"/api/sessions/{sid}/member-lookup", {"member_number": "12345678"}, format="json")

    r = c.post(f"/api/sessions/{sid}/order", {"order_number": "abc"}, format="json")
    assert r.status_code == 400
    assert r.data["error"]["code"] == "VALIDATION_ERROR"
    assert r.data["state"] == "ASK_ORDER"
