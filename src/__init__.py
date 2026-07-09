"""
SQLite database — sync SQLAlchemy.
Works on Streamlit Cloud (no external DB needed).
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean, DateTime, Float, Integer, JSON,
    String, Text, UniqueConstraint, create_engine, func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from src.core.config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


class Signal(Base):
    __tablename__ = "signals"
    id: Mapped[int]            = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str]        = mapped_column(String(10), nullable=False, index=True)
    market_name: Mapped[str]   = mapped_column(String(64))
    direction: Mapped[str]     = mapped_column(String(10))
    probability: Mapped[float] = mapped_column(Float)
    confidence: Mapped[str]    = mapped_column(String(10))
    entry_price: Mapped[Optional[float]] = mapped_column(Float)
    stop_loss:   Mapped[Optional[float]] = mapped_column(Float)
    take_profit_1: Mapped[Optional[float]] = mapped_column(Float)
    take_profit_2: Mapped[Optional[float]] = mapped_column(Float)
    risk_reward:   Mapped[Optional[float]] = mapped_column(Float)
    atr_value:     Mapped[Optional[float]] = mapped_column(Float)
    module_scores: Mapped[Optional[dict]]  = mapped_column(JSON)
    technical_bias: Mapped[Optional[str]]  = mapped_column(String(10))
    macro_bias:     Mapped[Optional[str]]  = mapped_column(String(10))
    cot_bias:       Mapped[Optional[str]]  = mapped_column(String(10))
    ai_reasoning:   Mapped[Optional[str]]  = mapped_column(Text)
    status: Mapped[str]        = mapped_column(String(20), default="active")
    alert_sent: Mapped[bool]   = mapped_column(Boolean, default=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    outcome_rr:    Mapped[Optional[float]] = mapped_column(Float)
    outcome_label: Mapped[Optional[str]]   = mapped_column(String(20))


class CentralBankStatement(Base):
    __tablename__ = "cb_statements"
    id: Mapped[int]          = mapped_column(Integer, primary_key=True)
    bank_code: Mapped[str]   = mapped_column(String(10), index=True)
    event_type: Mapped[str]  = mapped_column(String(30))
    event_date: Mapped[str]  = mapped_column(String(10), index=True)
    headline: Mapped[str]    = mapped_column(Text)
    full_text: Mapped[Optional[str]] = mapped_column(Text)
    tone: Mapped[Optional[str]]      = mapped_column(String(20))
    tone_score: Mapped[Optional[float]] = mapped_column(Float)
    rate_decision: Mapped[Optional[str]] = mapped_column(String(10))
    rate_level:    Mapped[Optional[float]] = mapped_column(Float)
    ai_reasoning:  Mapped[Optional[str]]   = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class IsmRelease(Base):
    __tablename__ = "ism_releases"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    manufacturing_pmi: Mapped[Optional[float]] = mapped_column(Float)
    services_pmi:      Mapped[Optional[float]] = mapped_column(Float)
    period_label:      Mapped[Optional[str]]   = mapped_column(String(20))
    entered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CotSnapshot(Base):
    __tablename__ = "cot_snapshots"
    __table_args__ = (UniqueConstraint("symbol", "report_date"),)
    id: Mapped[int]         = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str]     = mapped_column(String(10), index=True)
    report_date: Mapped[str]= mapped_column(String(10), index=True)
    commercials_net: Mapped[Optional[float]] = mapped_column(Float)
    large_specs_net: Mapped[Optional[float]] = mapped_column(Float)
    open_interest:   Mapped[Optional[float]] = mapped_column(Float)
    cot_index:       Mapped[Optional[float]] = mapped_column(Float)
    net_change_wk:   Mapped[Optional[float]] = mapped_column(Float)
    institutional_bias: Mapped[Optional[str]]  = mapped_column(String(10))
    bias_score:         Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


def get_db() -> Session:
    return SessionLocal()


def create_tables():
    Base.metadata.create_all(engine)
