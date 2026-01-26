"""Tests for the Mergington High School API."""

import pytest
from fastapi.testclient import TestClient


class TestRootEndpoint:
    """Test the root endpoint."""

    def test_root_redirects_to_static(self, client):
        """Test that root endpoint redirects to static/index.html."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestGetActivities:
    """Test the GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that GET /activities returns all available activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        # Verify expected activities are present
        expected_activities = [
            "Basketball Team",
            "Soccer Club",
            "Art Club",
            "Drama Club",
            "Debate Team",
            "Math Club",
            "Chess Club",
            "Programming Class",
            "Gym Class"
        ]
        
        for activity in expected_activities:
            assert activity in data
            assert "description" in data[activity]
            assert "schedule" in data[activity]
            assert "max_participants" in data[activity]
            assert "participants" in data[activity]

    def test_get_activities_structure(self, client, reset_activities):
        """Test that each activity has the correct structure."""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert isinstance(activity_data, dict)
            assert isinstance(activity_data["description"], str)
            assert isinstance(activity_data["schedule"], str)
            assert isinstance(activity_data["max_participants"], int)
            assert isinstance(activity_data["participants"], list)

    def test_get_activities_with_existing_participants(self, client, reset_activities):
        """Test that activities with existing participants are returned correctly."""
        response = client.get("/activities")
        data = response.json()
        
        # Chess Club should have existing participants
        chess_club = data["Chess Club"]
        assert len(chess_club["participants"]) == 2
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]


class TestSignupEndpoint:
    """Test the POST /activities/{activity_name}/signup endpoint."""

    def test_signup_for_existing_activity(self, client, reset_activities):
        """Test successful signup for an existing activity."""
        response = client.post(
            "/activities/Basketball Team/signup",
            params={"email": "john@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "john@mergington.edu" in data["message"]

    def test_signup_adds_participant(self, client, reset_activities):
        """Test that signup actually adds the participant to the activity."""
        client.post(
            "/activities/Soccer Club/signup",
            params={"email": "alice@mergington.edu"}
        )
        
        response = client.get("/activities")
        activities = response.json()
        assert "alice@mergington.edu" in activities["Soccer Club"]["participants"]

    def test_signup_for_nonexistent_activity(self, client, reset_activities):
        """Test signup for an activity that doesn't exist."""
        response = client.post(
            "/activities/Nonexistent Club/signup",
            params={"email": "john@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_duplicate_signup(self, client, reset_activities):
        """Test that duplicate signups are rejected."""
        # First signup
        response1 = client.post(
            "/activities/Art Club/signup",
            params={"email": "bob@mergington.edu"}
        )
        assert response1.status_code == 200
        
        # Duplicate signup
        response2 = client.post(
            "/activities/Art Club/signup",
            params={"email": "bob@mergington.edu"}
        )
        assert response2.status_code == 400
        data = response2.json()
        assert "already signed up" in data["detail"]

    def test_signup_existing_participant(self, client, reset_activities):
        """Test signup for a participant that's already in an activity."""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_multiple_different_signups(self, client, reset_activities):
        """Test multiple different signups."""
        emails = [f"student{i}@mergington.edu" for i in range(3)]
        
        for email in emails:
            response = client.post(
                "/activities/Math Club/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        response = client.get("/activities")
        activities = response.json()
        assert len(activities["Math Club"]["participants"]) == 3


class TestUnregisterEndpoint:
    """Test the POST /activities/{activity_name}/unregister endpoint."""

    def test_unregister_from_activity(self, client, reset_activities):
        """Test successful unregistration from an activity."""
        # First signup
        client.post(
            "/activities/Basketball Team/signup",
            params={"email": "charlie@mergington.edu"}
        )
        
        # Then unregister
        response = client.post(
            "/activities/Basketball Team/unregister",
            params={"email": "charlie@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        assert "charlie@mergington.edu" in data["message"]

    def test_unregister_removes_participant(self, client, reset_activities):
        """Test that unregister actually removes the participant."""
        # Signup
        client.post(
            "/activities/Drama Club/signup",
            params={"email": "david@mergington.edu"}
        )
        
        # Verify signup
        response = client.get("/activities")
        assert "david@mergington.edu" in response.json()["Drama Club"]["participants"]
        
        # Unregister
        client.post(
            "/activities/Drama Club/unregister",
            params={"email": "david@mergington.edu"}
        )
        
        # Verify removal
        response = client.get("/activities")
        assert "david@mergington.edu" not in response.json()["Drama Club"]["participants"]

    def test_unregister_from_nonexistent_activity(self, client, reset_activities):
        """Test unregister from an activity that doesn't exist."""
        response = client.post(
            "/activities/Nonexistent Club/unregister",
            params={"email": "john@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_unregister_not_registered_student(self, client, reset_activities):
        """Test unregister for a student not registered for the activity."""
        response = client.post(
            "/activities/Debate Team/unregister",
            params={"email": "eve@mergington.edu"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"]

    def test_unregister_existing_participant(self, client, reset_activities):
        """Test unregistering an existing participant."""
        response = client.post(
            "/activities/Programming Class/unregister",
            params={"email": "emma@mergington.edu"}
        )
        assert response.status_code == 200
        
        # Verify removal
        response = client.get("/activities")
        assert "emma@mergington.edu" not in response.json()["Programming Class"]["participants"]

    def test_cannot_unregister_twice(self, client, reset_activities):
        """Test that you cannot unregister twice."""
        # Signup
        client.post(
            "/activities/Chess Club/signup",
            params={"email": "frank@mergington.edu"}
        )
        
        # First unregister
        response1 = client.post(
            "/activities/Chess Club/unregister",
            params={"email": "frank@mergington.edu"}
        )
        assert response1.status_code == 200
        
        # Second unregister should fail
        response2 = client.post(
            "/activities/Chess Club/unregister",
            params={"email": "frank@mergington.edu"}
        )
        assert response2.status_code == 400
        data = response2.json()
        assert "not registered" in data["detail"]


class TestIntegration:
    """Integration tests for the full user workflow."""

    def test_complete_signup_workflow(self, client, reset_activities):
        """Test complete workflow: signup, verify, unregister."""
        activity = "Art Club"
        email = "grace@mergington.edu"
        
        # Get initial state
        response = client.get("/activities")
        initial_count = len(response.json()[activity]["participants"])
        
        # Signup
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify signup
        response = client.get("/activities")
        after_signup = response.json()[activity]["participants"]
        assert email in after_signup
        assert len(after_signup) == initial_count + 1
        
        # Unregister
        response = client.post(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify unregister
        response = client.get("/activities")
        after_unregister = response.json()[activity]["participants"]
        assert email not in after_unregister
        assert len(after_unregister) == initial_count

    def test_multiple_students_signup_same_activity(self, client, reset_activities):
        """Test multiple students signing up for the same activity."""
        activity = "Gym Class"
        students = ["student1@test.edu", "student2@test.edu", "student3@test.edu"]
        
        for student in students:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": student}
            )
            assert response.status_code == 200
        
        response = client.get("/activities")
        participants = response.json()[activity]["participants"]
        for student in students:
            assert student in participants
