from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    original_activities = deepcopy(activities)
    with TestClient(app) as test_client:
        yield test_client
    activities.clear()
    activities.update(original_activities)


def test_get_activities_returns_activity_details(client):
    response = client.get("/activities")

    assert response.status_code == 200
    activities_response = response.json()
    assert "Chess Club" in activities_response
    assert activities_response["Chess Club"]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_signup_is_visible_in_fresh_activities_response(client):
    email = "new.student@mergington.edu"
    signup_response = client.post(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    assert signup_response.status_code == 200
    assert signup_response.json()["message"] == f"Signed up {email} for Chess Club"

    activities_response = client.get("/activities")

    assert email in activities_response.json()["Chess Club"]["participants"]


def test_duplicate_signup_returns_400_without_changing_participants(client):
    email = "michael@mergington.edu"
    participants_before = client.get("/activities").json()["Chess Club"]["participants"]

    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"
    assert client.get("/activities").json()["Chess Club"]["participants"] == participants_before


def test_signup_for_unknown_activity_returns_404(client):
    response = client.post(
        "/activities/Unknown Activity/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_is_visible_in_fresh_activities_response(client):
    email = "michael@mergington.edu"
    response = client.delete(
        "/activities/Chess Club/participants",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json()["message"] == f"Unregistered {email} from Chess Club"

    activities_response = client.get("/activities")

    assert email not in activities_response.json()["Chess Club"]["participants"]


def test_unregister_nonparticipant_returns_404(client):
    response = client.delete(
        "/activities/Chess Club/participants",
        params={"email": "not.signed.up@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_unregister_from_unknown_activity_returns_404(client):
    response = client.delete(
        "/activities/Unknown Activity/participants",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"