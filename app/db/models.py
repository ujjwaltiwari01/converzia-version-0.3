"""
SQLAlchemy Relational Database Models
-------------------------------------
Defines the enterprise schema for Converzia:
1. Lead: Target prospect profiles enriched with website intelligence & brand voice.
2. Campaign: High-volume outreach campaigns with target ICPs & daily pacing.
3. SequenceStep: Multi-stage cadences (Initial -> Case Study -> Breakup).
4. OutreachLog: Full audit log of generated emails, delivery state, open/click telemetry.
5. SDRAgentDecision: Autonomous SDR agent reasoning, sentiment classification, and objection handling.

INTERVIEW TALKING POINT:
- Clean normalization: Decouples lead contact data from campaign cadences and telemetry.
- Telemetry tracking: Uses indexed tracking tokens for sub-millisecond open pixel and click redirect lookups.
"""

from datetime import datetime, timezone
import uuid
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float, ForeignKey, Boolean, JSON
)
from sqlalchemy.orm import relationship
from app.db.session import Base

def utc_now():
    return datetime.now(timezone.utc)


class Lead(Base):
    """Stores B2B prospect information and scraped brand intelligence."""
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    company_name = Column(String(150), index=True, nullable=True)
    website_url = Column(String(500), nullable=True)
    industry = Column(String(100), nullable=True)
    keywords = Column(String(255), nullable=True)

    # Scraped Website Intelligence
    scraped_title = Column(String(500), nullable=True)
    scraped_meta_desc = Column(Text, nullable=True)
    scraped_summary = Column(Text, nullable=True)
    scraped_at = Column(DateTime, nullable=True)

    # LangChain Extracted Brand Voice & ICP Profile
    brand_voice_summary = Column(JSON, nullable=True)

    # Outreach Lifecycle Status
    # NEW | ENRICHED | IN_SEQUENCE | REPLIED | MEETING_SET | BOUNCED | OPT_OUT
    status = Column(String(50), default="NEW", index=True)

    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    outreach_logs = relationship("OutreachLog", back_populates="lead", cascade="all, delete-orphan")
    sdr_decisions = relationship("SDRAgentDecision", back_populates="lead", cascade="all, delete-orphan")


class Campaign(Base):
    """Manages B2B outreach campaigns and daily pacing limits (e.g. 1,000 leads/day)."""
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    target_icp = Column(String(255), default="B2B Agency Decision Makers")
    value_proposition = Column(Text, nullable=True)
    daily_lead_limit = Column(Integer, default=1000)
    status = Column(String(50), default="ACTIVE", index=True)  # ACTIVE, PAUSED, COMPLETED

    created_at = Column(DateTime, default=utc_now)

    # Relationships
    sequences = relationship("SequenceStep", back_populates="campaign", cascade="all, delete-orphan")
    outreach_logs = relationship("OutreachLog", back_populates="campaign")


class SequenceStep(Base):
    """Defines each step in an automated multi-stage SDR cadence."""
    __tablename__ = "sequence_steps"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    step_number = Column(Integer, nullable=False)  # 1 = Initial Outreach, 2 = Value-add, 3 = Breakup
    delay_days = Column(Integer, default=2)       # Delay before dispatching next step
    step_type = Column(String(50), default="INITIAL")  # INITIAL, FOLLOWUP_OPENED, FOLLOWUP_UNOPENED, BREAKUP
    prompt_focus = Column(Text, nullable=True)

    # Relationships
    campaign = relationship("Campaign", back_populates="sequences")


class OutreachLog(Base):
    """Complete audit and telemetry log for every email generated and sent."""
    __tablename__ = "outreach_logs"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True)
    sequence_step = Column(Integer, default=1)

    # Email Content
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    spam_score = Column(Float, default=0.0)  # Deliverability safety index (0 = clean, 100 = high risk)

    # Telemetry Identifiers
    tracking_token = Column(String(64), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # State: GENERATED | SCHEDULED | SENT | DELIVERED | OPENED | CLICKED | REPLIED | FAILED
    status = Column(String(50), default="GENERATED", index=True)

    # Engagement Timestamps
    sent_at = Column(DateTime, nullable=True)
    opened_at = Column(DateTime, nullable=True)
    clicked_at = Column(DateTime, nullable=True)
    replied_at = Column(DateTime, nullable=True)
    open_count = Column(Integer, default=0)
    click_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=utc_now)

    # Relationships
    lead = relationship("Lead", back_populates="outreach_logs")
    campaign = relationship("Campaign", back_populates="outreach_logs")


class SDRAgentDecision(Base):
    """Audit log of Autonomous SDR Agent reasoning, classification, and next-step execution."""
    __tablename__ = "sdr_agent_decisions"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    outreach_log_id = Column(Integer, ForeignKey("outreach_logs.id"), nullable=True)

    prospect_input_event = Column(String(100), default="REPLY_RECEIVED")
    prospect_reply_text = Column(Text, nullable=True)

    # Sentiment / Intent Classification
    classification = Column(String(100), nullable=False)
    confidence_score = Column(Float, default=0.9)

    # LangChain Agent Reasoning Chain of Thought
    reasoning = Column(Text, nullable=True)

    # Action Decided
    recommended_action = Column(String(100), nullable=False)
    generated_response = Column(Text, nullable=True)
    is_executed = Column(Boolean, default=False)

    created_at = Column(DateTime, default=utc_now)

    # Relationships
    lead = relationship("Lead", back_populates="sdr_decisions")
