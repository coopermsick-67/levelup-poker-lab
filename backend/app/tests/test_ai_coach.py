"""Tests for the AI Coach module (M5)."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.database import Base
from app.models.user import User
from app.services.ai_coach.report import CoachReport, _classify_player, _find_strengths


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def engine():
    """Create an in-memory SQLite engine for testing."""
    eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=eng)
    return eng


@pytest.fixture
def db(engine):
    """Yield a SQLAlchemy session backed by the in-memory engine."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_user(db: Session) -> User:
    """Persist a test user and return it."""
    user = User(
        display_name="Test Player",
        username="testplayer",
        hashed_password="fakehash",
        level=3,
        xp=150,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# Helper: build a fake stats dict
# ---------------------------------------------------------------------------

def _make_stats(
    vpip: float = 22.0,
    pfr: float = 14.0,
    three_bet_pct: float = 5.0,
    cbet_pct: float = 55.0,
    aggression_factor: float = 2.0,
    wwsf_pct: float = 42.0,
    total_hands: int = 50,
    fold_to_3bet_pct: float = 60.0,
    fold_to_cbet_pct: float = 50.0,
    total_decisions: int = 200,
    btn_vpip: float = 30.0,
    utg_vpip: float = 15.0,
):
    return {
        "vpip": vpip,
        "pfr": pfr,
        "three_bet_pct": three_bet_pct,
        "fold_to_3bet_pct": fold_to_3bet_pct,
        "cbet_pct": cbet_pct,
        "fold_to_cbet_pct": fold_to_cbet_pct,
        "aggression_factor": aggression_factor,
        "wwsf_pct": wwsf_pct,
        "total_hands": total_hands,
        "total_decisions": total_decisions,
        "position_stats": {
            "UTG": {"hands": 20, "vpip": utg_vpip, "pfr": 10.0},
            "MP": {"hands": 15, "vpip": 20.0, "pfr": 12.0},
            "CO": {"hands": 15, "vpip": 25.0, "pfr": 15.0},
            "BTN": {"hands": 15, "vpip": btn_vpip, "pfr": 20.0},
            "SB": {"hands": 10, "vpip": 22.0, "pfr": 8.0},
            "BB": {"hands": 10, "vpip": 18.0, "pfr": 6.0},
        },
    }


# ---------------------------------------------------------------------------
# Tests: player classification
# ---------------------------------------------------------------------------

class TestClassifyPlayer:
    def test_nit(self):
        stats = _make_stats(vpip=14.0, pfr=6.0, aggression_factor=0.8)
        assert _classify_player(stats) == "nit"

    def test_tag(self):
        stats = _make_stats(vpip=22.0, pfr=15.0, aggression_factor=2.0)
        assert _classify_player(stats) == "tag"

    def test_lag(self):
        stats = _make_stats(vpip=30.0, pfr=22.0, aggression_factor=3.0)
        assert _classify_player(stats) == "lag"

    def test_maniac(self):
        stats = _make_stats(vpip=40.0, pfr=30.0, aggression_factor=5.5)
        assert _classify_player(stats) == "maniac"

    def test_default_low_sample(self):
        stats = _make_stats(total_hands=2)
        assert _classify_player(stats) == "default"


# ---------------------------------------------------------------------------
# Tests: strengths detection
# ---------------------------------------------------------------------------

class TestFindStrengths:
    def test_returns_list(self):
        stats = _make_stats()
        strengths = _find_strengths(stats)
        assert isinstance(strengths, list)
        assert len(strengths) >= 1
        assert len(strengths) <= 3

    def test_empty_stats_returns_fallback(self):
        stats = _make_stats(vpip=0, pfr=0, wwsf_pct=0, total_hands=0, btn_vpip=0, utg_vpip=0)
        strengths = _find_strengths(stats)
        assert len(strengths) >= 1

    def test_good_player_gets_multiple_strengths(self):
        stats = _make_stats(vpip=22.0, pfr=14.0, aggression_factor=2.0, wwsf_pct=45.0, three_bet_pct=6.0)
        strengths = _find_strengths(stats)
        assert len(strengths) >= 2


# ---------------------------------------------------------------------------
# Tests: CoachReport.generate
# ---------------------------------------------------------------------------

class TestCoachReport:
    def test_generate_no_data(self, db: Session, sample_user: User):
        """Report generates gracefully for a user with no hand data."""
        report = CoachReport()
        result = report.generate(user_id=sample_user.id, db=db)

        assert isinstance(result, dict)
        assert "summary" in result
        assert "leaks" in result
        assert "strengths" in result
        assert "training_plan" in result
        assert "stats_snapshot" in result
        assert "archetype" in result

    def test_generate_nonexistent_user(self, db: Session):
        """Report generates gracefully for a user that doesn't exist."""
        report = CoachReport()
        result = report.generate(user_id=9999, db=db)

        assert isinstance(result, dict)
        assert result["archetype"] == "unknown"
        assert "User not found" in result["summary"]

    def test_report_structure(self, db: Session, sample_user: User):
        """Report has all required keys and correct types."""
        report = CoachReport()
        result = report.generate(user_id=sample_user.id, db=db)

        # Check all required keys
        required_keys = {"summary", "archetype", "leaks", "strengths", "training_plan", "stats_snapshot"}
        assert required_keys.issubset(result.keys())

        # Check types
        assert isinstance(result["summary"], str)
        assert len(result["summary"]) > 10  # Not empty
        assert isinstance(result["archetype"], str)
        assert isinstance(result["leaks"], list)
        assert isinstance(result["strengths"], list)
        assert isinstance(result["training_plan"], list)
        assert isinstance(result["stats_snapshot"], dict)

    def test_stats_snapshot_keys(self, db: Session, sample_user: User):
        """Stats snapshot contains expected metrics."""
        report = CoachReport()
        result = report.generate(user_id=sample_user.id, db=db)

        snapshot = result["stats_snapshot"]
        expected_keys = {"total_hands", "vpip", "pfr", "three_bet_pct", "cbet_pct", "aggression_factor", "wwsf_pct"}
        assert expected_keys.issubset(snapshot.keys())

    def test_training_plan_has_drill_info(self, db: Session, sample_user: User):
        """Each training plan entry has name, description, url, and reason."""
        report = CoachReport()
        result = report.generate(user_id=sample_user.id, db=db)

        for drill in result["training_plan"]:
            assert "name" in drill
            assert "description" in drill
            assert "url" in drill
            assert "reason" in drill

    def test_leaks_capped_at_five(self, db: Session, sample_user: User):
        """Report should include at most 5 leaks."""
        report = CoachReport()
        result = report.generate(user_id=sample_user.id, db=db)
        assert len(result["leaks"]) <= 5

    def test_strengths_capped_at_three(self, db: Session, sample_user: User):
        """Report should include at most 3 strengths."""
        report = CoachReport()
        result = report.generate(user_id=sample_user.id, db=db)
        assert len(result["strengths"]) <= 3

    def test_training_plan_capped_at_three(self, db: Session, sample_user: User):
        """Report should include at most 3 training plan items."""
        report = CoachReport()
        result = report.generate(user_id=sample_user.id, db=db)
        assert len(result["training_plan"]) <= 3

    def test_summary_is_personalised(self, db: Session, sample_user: User):
        """Summary should mention actual stat values."""
        report = CoachReport()
        result = report.generate(user_id=sample_user.id, db=db)

        # With no data, summary should mention 0% or similar
        summary = result["summary"]
        assert "%" in summary  # Contains percentage values
