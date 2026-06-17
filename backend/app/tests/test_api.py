"""API integration tests using FastAPI TestClient."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

# In-memory SQLite for testing
TEST_DB = "sqlite:///./test_api.db"
engine = create_engine(TEST_DB, connect_args={"check_same_thread": False})
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def _setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    session = TestSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db):
    def _override():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _register_and_login(client: TestClient, username: str = "testuser") -> str:
    """Helper: register + login, return token."""
    client.post("/api/auth/register", json={
        "display_name": "Test Player",
        "username": username,
        "password": "pass",
    })
    resp = client.post("/api/auth/login", json={
        "username": username,
        "password": "pass",
    })
    return resp.json()["access_token"]


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class TestAuth:
    def test_register(self, client):
        resp = client.post("/api/auth/register", json={
            "display_name": "New Player",
            "username": "newuser",
            "password": "pass123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["user"]["username"] == "newuser"

    def test_login(self, client):
        token = _register_and_login(client, "loginuser")
        # Re-login with same credentials
        resp = client.post("/api/auth/login", json={
            "username": "loginuser",
            "password": "pass",
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_login_wrong_password(self, client):
        _register_and_login(client, "wrongpass")
        resp = client.post("/api/auth/login", json={
            "username": "wrongpass",
            "password": "x",
        })
        assert resp.status_code == 401

    def test_me(self, client):
        token = _register_and_login(client, "meuser")
        resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["username"] == "meuser"


# ---------------------------------------------------------------------------
# Play
# ---------------------------------------------------------------------------

class TestPlay:
    def test_create_table(self, client):
        token = _register_and_login(client, "playuser")
        resp = client.post("/api/play/tables", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert "table_id" in data
        assert data["table"]["hero_seat_index"] == 0
        hero_seat = data["table"]["seats"][data["table"]["hero_seat_index"]]
        assert hero_seat["stack"] == 1000

    def test_start_hand(self, client):
        token = _register_and_login(client, "starthand")
        create = client.post("/api/play/tables", headers={"Authorization": f"Bearer {token}"}).json()
        table_id = create["table_id"]
        resp = client.post(f"/api/play/tables/{table_id}/start", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["current_street"] == 0
        assert "legal_actions" in data

    def test_invalid_token(self, client):
        resp = client.post("/api/play/tables", headers={"Authorization": "Bearer invalid.token.value"})
        assert resp.status_code == 401

    def test_table_not_found(self, client):
        token = _register_and_login(client, "notfound")
        resp = client.get("/api/play/tables/fakeid", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Drills
# ---------------------------------------------------------------------------

class TestDrills:
    def test_create_session(self, client):
        token = _register_and_login(client, "drilluser")
        resp = client.post("/api/drills/session", json={
            "drill_type": "preflop",
            "count": 5,
        }, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["session"]["drill_type"] == "preflop"
        assert data["session"]["total_questions"] == 5
        assert len(data["drills"]) == 5

    def test_grade_answer(self, client):
        token = _register_and_login(client, "gradeuser")
        session_resp = client.post("/api/drills/session", json={
            "drill_type": "preflop",
            "count": 5,
        }, headers={"Authorization": f"Bearer {token}"}).json()
        drill = session_resp["drills"][0]
        resp = client.post("/api/drills/answer", json={
            "session_id": session_resp["session"]["id"],
            "drill_id": drill["id"],
            "answer": drill["correct_action"],
        }, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["correct"] is True
        assert "feedback" in data

    def test_session_results(self, client):
        token = _register_and_login(client, "resultsuser")
        session_resp = client.post("/api/drills/session", json={
            "drill_type": "preflop",
            "count": 3,
        }, headers={"Authorization": f"Bearer {token}"}).json()
        drill = session_resp["drills"][0]
        client.post("/api/drills/answer", json={
            "session_id": session_resp["session"]["id"],
            "drill_id": drill["id"],
            "answer": drill["correct_action"],
        }, headers={"Authorization": f"Bearer {token}"})
        resp = client.get(f"/api/drills/session/{session_resp['session']['id']}/results",
                         headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["answered"] == 1
        assert data["correct"] == 1


# ---------------------------------------------------------------------------
# Review
# ---------------------------------------------------------------------------

class TestReview:
    def test_stats_empty(self, client):
        token = _register_and_login(client, "statsuser")
        resp = client.get("/api/review/stats", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_hands"] == 0
        assert data["vpip"] == 0

    def test_leaks_empty(self, client):
        token = _register_and_login(client, "leaksuser")
        resp = client.get("/api/review/leaks", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_summary(self, client):
        token = _register_and_login(client, "summaryuser")
        resp = client.get("/api/review/summary", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert "stats" in data
        assert "leaks" in data

    def test_coach_report(self, client):
        token = _register_and_login(client, "coachuser")
        resp = client.get("/api/review/coach-report", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert "summary" in data
        assert "archetype" in data
        assert "strengths" in data
        assert "training_plan" in data


# ---------------------------------------------------------------------------
# Gamification
# ---------------------------------------------------------------------------

class TestGamification:
    def test_profile(self, client):
        token = _register_and_login(client, "profileuser")
        resp = client.get("/api/gamification/profile", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["level"] == 1
        assert data["xp"] == 0
        assert "badges" in data
        assert "total_hands" in data

    def test_profile_total_hands_zero_for_new_user(self, client):
        """New user with no hands should have total_hands=0, not 1."""
        token = _register_and_login(client, "newhands")
        resp = client.get("/api/gamification/profile", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_hands"] == 0

    def test_quests(self, client):
        token = _register_and_login(client, "questuser")
        resp = client.get("/api/gamification/quests", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert "quests" in data
        assert len(data["quests"]) > 0

    def test_leaderboard(self, client):
        token = _register_and_login(client, "leaderuser")
        resp = client.get("/api/gamification/leaderboard", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert "leaderboard" in data
        assert "user_rank" in data

    def test_event_awards_xp(self, client):
        token = _register_and_login(client, "eventuser")
        resp = client.post("/api/gamification/event?event_type=play_hand",
                          headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["xp"]["xp_earned"] == 10

    def test_claim_daily(self, client):
        token = _register_and_login(client, "dailyuser")
        resp = client.post("/api/gamification/claim-daily",
                          headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["xp_earned"] == 5
        assert data["streak"] >= 1


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

class TestHealth:
    def test_health(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
