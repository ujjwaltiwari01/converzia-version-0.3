"""
Pydantic Schemas for Autonomous SDR Agent
-----------------------------------------
Defines request and response contracts for the SDR Agent:
Intent classification, objection handling, and autonomous sequencing decisions.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class SDRClassifyRequest(BaseModel):
    lead_id: int = Field(..., description="Target lead database ID")
    prospect_reply_text: str = Field(..., description="Incoming prospect reply email text")
    previous_email_subject: Optional[str] = None
    previous_email_body: Optional[str] = None


class SDRDecisionResponse(BaseModel):
    lead_id: int
    classification: str = Field(
        ...,
        description="INTERESTED | MEETING_REQUESTED | OBJECTION_PRICING | OBJECTION_TIMING | OBJECTION_COMPETITOR | OUT_OF_OFFICE | UNSUBSCRIBE | NOT_INTERESTED"
    )
    confidence_score: float
    reasoning: str = Field(..., description="LLM Chain-of-Thought explaining the classification & action rationale")
    recommended_action: str = Field(
        ...,
        description="SEND_CALENDAR_LINK | DRAFT_OBJECTION_HANDLING | PAUSE_CADENCE | RESCHEDULE_OOF | OPT_OUT"
    )
    suggested_reply: Optional[str] = None
    next_sequence_step: Optional[int] = None
    delay_hours_before_send: int = 0


class BatchSDRRunRequest(BaseModel):
    campaign_id: Optional[int] = None
    max_leads_to_process: int = Field(100, ge=1, le=1000)
    dry_run: bool = Field(True, description="If True, generates emails and logs decisions without sending")


class BatchSDRRunResponse(BaseModel):
    total_processed: int
    emails_generated: int
    emails_dispatched: int
    skipped_or_paused: int
    execution_time_seconds: float
    summary: List[str]
