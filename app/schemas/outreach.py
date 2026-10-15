"""
Pydantic Schemas for Outreach & Telemetry
-----------------------------------------
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


class GenerateEmailRequest(BaseModel):
    lead_id: Optional[int] = Field(None, description="Existing Lead ID in database")
    company_name: Optional[str] = Field(None, description="Company name if generating ad-hoc")
    website_url: Optional[str] = Field(None, description="Website URL to scrape on-the-fly")
    recipient_name: Optional[str] = Field(None, description="Recipient contact name")
    keywords: Optional[str] = Field(None, description="Industry or focus keywords")
    sequence_step: int = Field(1, description="1 for cold intro, 2 for value follow-up, 3 for breakup")
    prev_subject: Optional[str] = Field(None, description="Required for follow-up emails")
    prev_body: Optional[str] = Field(None, description="Required for follow-up emails")


class EmailPreviewResponse(BaseModel):
    subject: str
    body: str
    alternative_subjects: List[str] = []
    spam_score: float
    spam_reasons: List[str] = []
    personalization_hook: str
    target_company: str


class SendEmailRequest(BaseModel):
    lead_id: int
    subject: str
    body: str
    campaign_id: Optional[int] = None
    sequence_step: int = 1


class SendEmailResponse(BaseModel):
    outreach_log_id: int
    recipient_email: str
    status: str
    tracking_token: str
    message: str


class TrackingEventPayload(BaseModel):
    token: str
    event_type: str = Field(..., description="'open' or 'click'")
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
