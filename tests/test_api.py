"""
Tests for High School Management System API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI application"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test"""
    # Reset participants for all activities
    activities["Soccer Team"]["participants"] = []
    activities["Basketball Club"]["participants"] = []
    activities["Art Club"]["participants"] = []
    activities["Drama Society"]["participants"] = []
    activities["Math Olympiad"]["participants"] = []
    activities["Debate Club"]["participants"] = []
    activities["Chess Club"]["participants"] = ["michael@mergington.edu", "daniel@mergington.edu"]
    activities["Programming Class"]["participants"] = ["emma@mergington.edu", "sophia@mergington.edu"]
    activities["Gym Class"]["participants"] = ["john@mergington.edu", "olivia@mergington.edu"]
    yield


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirects_to_static_index(self, client):
        """Test that root path redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for the GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """Test that all activities are returned"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        # Check that all expected activities are present
        expected_activities = [
            "Soccer Team", "Basketball Club", "Art Club", "Drama Society",
            "Math Olympiad", "Debate Club", "Chess Club", "Programming Class", "Gym Class"
        ]
        for activity in expected_activities:
            assert activity in data

    def test_get_activities_returns_correct_structure(self, client):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        # Check structure of one activity
        soccer = data["Soccer Team"]
        assert "description" in soccer
        assert "schedule" in soccer
        assert "max_participants" in soccer
        assert "participants" in soccer
        assert isinstance(soccer["participants"], list)

    def test_get_activities_includes_existing_participants(self, client):
        """Test that activities with participants return them correctly"""
        response = client.get("/activities")
        data = response.json()
        
        # Check Chess Club has initial participants
        chess_club = data["Chess Club"]
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]


class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Soccer Team/signup?email=student@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "student@mergington.edu" in data["message"]
        assert "Soccer Team" in data["message"]
        
        # Verify student was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "student@mergington.edu" in activities_data["Soccer Team"]["participants"]

    def test_signup_with_url_encoded_activity_name(self, client):
        """Test signup with URL-encoded activity name"""
        response = client.post(
            "/activities/Basketball%20Club/signup?email=alice@mergington.edu"
        )
        assert response.status_code == 200
        
        # Verify student was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "alice@mergington.edu" in activities_data["Basketball Club"]["participants"]

    def test_signup_activity_not_found(self, client):
        """Test signup for non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_signup_already_signed_up(self, client):
        """Test that signing up twice for same activity returns 400"""
        email = "test@mergington.edu"
        
        # First signup
        response1 = client.post(f"/activities/Art Club/signup?email={email}")
        assert response1.status_code == 200
        
        # Second signup (should fail)
        response2 = client.post(f"/activities/Art Club/signup?email={email}")
        assert response2.status_code == 400
        data = response2.json()
        assert "detail" in data
        assert "already signed up" in data["detail"].lower()

    def test_signup_multiple_students(self, client):
        """Test that multiple students can sign up for same activity"""
        emails = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu"
        ]
        
        for email in emails:
            response = client.post(f"/activities/Drama Society/signup?email={email}")
            assert response.status_code == 200
        
        # Verify all students were added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        drama_participants = activities_data["Drama Society"]["participants"]
        
        for email in emails:
            assert email in drama_participants


class TestRemoveParticipant:
    """Tests for the DELETE /activities/{activity_name}/participants/{email} endpoint"""

    def test_remove_participant_success(self, client):
        """Test successful removal of a participant"""
        # First, sign up a student
        email = "toremove@mergington.edu"
        client.post(f"/activities/Math Olympiad/signup?email={email}")
        
        # Now remove them
        response = client.delete(f"/activities/Math%20Olympiad/participants/{email}")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        
        # Verify student was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email not in activities_data["Math Olympiad"]["participants"]

    def test_remove_existing_participant(self, client):
        """Test removal of a participant that was already enrolled"""
        # Chess Club has michael@mergington.edu as initial participant
        response = client.delete(
            "/activities/Chess%20Club/participants/michael@mergington.edu"
        )
        assert response.status_code == 200
        
        # Verify student was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "michael@mergington.edu" not in activities_data["Chess Club"]["participants"]

    def test_remove_participant_activity_not_found(self, client):
        """Test removal from non-existent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent%20Activity/participants/student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_remove_participant_not_enrolled(self, client):
        """Test removal of non-enrolled participant returns 404"""
        response = client.delete(
            "/activities/Soccer%20Team/participants/notenrolled@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not enrolled" in data["detail"].lower()

    def test_remove_participant_with_url_encoding(self, client):
        """Test removal with URL-encoded email and activity name"""
        # Sign up with email containing special characters
        import urllib.parse
        email = "test+user@mergington.edu"
        encoded_email = urllib.parse.quote(email, safe='')
        
        # Sign up with properly encoded email
        client.post(f"/activities/Debate%20Club/signup?email={encoded_email}")
        
        # Remove with URL encoding
        response = client.delete(
            f"/activities/Debate%20Club/participants/{encoded_email}"
        )
        assert response.status_code == 200


class TestIntegrationScenarios:
    """Integration tests covering complete user flows"""

    def test_complete_signup_and_removal_flow(self, client):
        """Test complete flow: view activities, signup, verify, remove, verify"""
        email = "integration@mergington.edu"
        activity = "Basketball Club"
        
        # 1. Get initial activities
        response = client.get("/activities")
        initial_data = response.json()
        initial_count = len(initial_data[activity]["participants"])
        
        # 2. Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # 3. Verify signup
        response = client.get("/activities")
        data = response.json()
        assert email in data[activity]["participants"]
        assert len(data[activity]["participants"]) == initial_count + 1
        
        # 4. Remove participant
        remove_response = client.delete(
            f"/activities/{activity}/participants/{email}"
        )
        assert remove_response.status_code == 200
        
        # 5. Verify removal
        response = client.get("/activities")
        final_data = response.json()
        assert email not in final_data[activity]["participants"]
        assert len(final_data[activity]["participants"]) == initial_count

    def test_max_participants_tracking(self, client):
        """Test that max_participants value is correct"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert activity_data["max_participants"] > 0
            # Participants should not exceed max (though we don't enforce this in the API yet)
            assert len(activity_data["participants"]) <= activity_data["max_participants"]
