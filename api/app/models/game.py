from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, func
from sqlalchemy.orm import relationship
from app.database import Base


class PokerTable(Base):
    __tablename__ = "poker_tables"

    id = Column(Integer, primary_key=True, autoincrement=True)
    table_id = Column(String(20), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    bot_styles = Column(String(100), default="nit,reg,maniac,reg,nit")
    small_blind = Column(Integer, default=5)
    big_blind = Column(Integer, default=10)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.now())


class Hand(Base):
    __tablename__ = "hands"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    table_id = Column(String(20), nullable=False)
    hand_number = Column(Integer, nullable=False)
    hero_position = Column(Integer, nullable=False)
    hero_cards = Column(String(10))
    community_cards = Column(String(20))
    pot_size = Column(Integer, default=0)
    result = Column(String(20))  # win, loss, fold
    chips_change = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="hands")
    decisions = relationship("HandDecision", back_populates="hand")


class HandDecision(Base):
    __tablename__ = "hand_decisions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    hand_id = Column(Integer, ForeignKey("hands.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    street = Column(String(10), nullable=False)  # preflop, flop, turn, river
    position = Column(String(5), nullable=False)  # UTG, MP, CO, BTN, SB, BB
    hole_cards = Column(String(10))
    community_cards = Column(String(20))
    pot_size = Column(Integer, default=0)
    stack_size = Column(Integer, default=0)
    action_taken = Column(String(10), nullable=False)  # fold, check, call, raise, all_in
    amount = Column(Integer, default=0)
    was_correct = Column(Integer, nullable=True)  # 1=yes, 0=no, null=N/A
    ev_diff = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    hand = relationship("Hand", back_populates="decisions")


class DrillSession(Base):
    __tablename__ = "drill_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    drill_type = Column(String(20), nullable=False)  # preflop, postflop
    total_questions = Column(Integer, nullable=False, default=10)
    created_at = Column(DateTime, server_default=func.now())

    attempts = relationship("DrillAttempt", back_populates="session")


class DrillAttempt(Base):
    __tablename__ = "drill_attempts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("drill_sessions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    drill_id = Column(String(20), nullable=False)
    user_answer = Column(String(20), nullable=False)
    correct = Column(Integer, nullable=False, default=0)  # 1=yes, 0=no
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    session = relationship("DrillSession", back_populates="attempts")
