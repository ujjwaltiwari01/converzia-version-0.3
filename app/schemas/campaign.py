"""
Pydantic Schemas for Campaigns and Sequence Steps
-------------------------------------------------
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class SequenceStepCreate(BaseModel):
    step_number: int = Field(..., ge=1, le=10, description="Order of step in sequence")
    delay_days: int = Field(2, ge=0, description="Days to wait after previous step")
    step_type: str = Field("INITIAL", description="INITIAL, FOLLOWUP_OPENED, FOLLOWUP_UNOPENED, BREAKUP")
    prompt_focus: Optional[str] = Field(None, description="Specific angle, case study, or CTA for this step")


class SequenceStepResponse(SequenceStepCreate):
    id: int
    campaign_id: int

    model_config = ConfigDict(from_attributes=True)


class CampaignCreate(BaseModel):
    name: str = Field(..., max_length=150, description="Campaign identifier name")
    description: Optional[str] = None
    target_icp: str = Field("B2B Marketing & SaaS Agencies", description="Ideal Customer Profile definition")
    value_proposition: str = Field(..., description="Core value proposition of your product")
    daily_lead_limit: int = Field(1000, ge=1, le=5000, description="Maximum emails dispatched per day")
    sequences: Optional[List[SequenceStepCreate]] = None


class CampaignResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    target_icp: str
    value_proposition: Optional[str] = None
    daily_lead_limit: int
    status: str
    created_at: datetime
    sequences: List[SequenceStepResponse] = []

    model_config = ConfigDict(from_attributes=True)


class CampaignMetricsResponse(BaseModel):
    campaign_id: int
    total_leads: int
    emails_sent: int
    emails_opened: int
    emails_clicked: int
    emails_replied: int
    open_rate_percent: float
    click_rate_percent: float
    reply_rate_percent: float
    benchmark_comparison: str
