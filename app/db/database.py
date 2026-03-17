from __future__ import annotations
from sqlalchemy import Column, Integer, String, Float, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from typing import Generator

DATABASE_URL = "sqlite:///./a2a_core.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class AgentModel(Base):
    __tablename__ = "agents"
    agent_id = Column(String, primary_key=True, index=True)
    org_id = Column(String)
    domain = Column(String)
    payment_alias = Column(String, nullable=True)
    endpoint = Column(String, nullable=True)
    trust_tier = Column(String)
    protocol_versions = Column(Text)
    message_types = Column(Text)
    input_schemas = Column(Text)
    output_schemas = Column(Text)
    tools = Column(Text)
    max_latency_ms = Column(Integer)
    created_at = Column(String)


class MessageModel(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String, index=True)
    payload_hash = Column(String)
    canonical_hash = Column(String)
    domain = Column(String)
    created_at = Column(String)


class ReceiptModel(Base):
    __tablename__ = "receipts"
    request_id = Column(String, primary_key=True, index=True)
    receipt_status = Column(String)
    receiver_agent_id = Column(String)
    timestamp = Column(String)
    payload_hash = Column(String)
    execution_ref = Column(String, nullable=True)
    error_code = Column(String, nullable=True)
    error_message = Column(String, nullable=True)


class ReputationEventModel(Base):
    __tablename__ = "reputation_events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    subject_id = Column(String, index=True)
    event_type = Column(String)
    domain = Column(String)
    timestamp = Column(String)
    weight = Column(Float, default=1.0)
    evidence_ref = Column(String, nullable=True)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
