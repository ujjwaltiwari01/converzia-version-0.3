"""
Pydantic Schemas for Leads
--------------------------
Handles input validation, enrichment payloads, and response formatting for B2B leads.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class LeadBase(BaseModel):
    email: EmailStr = Field(..., description="Prospect business email address")
    first_name: Optional[str] = Field(None, description="Prospect first name")
    last_name: Optional[str] = Field(None, description="Prospect last name")
    company_name: Optional[str] = Field(None, description="Company / Organization name")
    website_url: Optional[str] = Field(None, description="Prospect company website URL")
    industry: Optional[str] = Field(None, description="Industry sector (e.g. SaaS, Digital Marketing)")
    keywords: Optional[str] = Field(None, description="Keywords or niche tags")


class LeadCreate(LeadBase):
    pass


class LeadUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    website_url: Optional[str] = None
    industry: Optional[str] = None
    keywords: Optional[str] = None
    status: Optional[str] = None


class LeadResponse(LeadBase):
    id: int
    status: str
    scraped_title: Optional[str] = None
    scraped_meta_desc: Optional[str] = None
    scraped_summary: Optional[str] = None
    brand_voice_summary: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LeadBatchUploadResponse(BaseModel):
    total_received: int
    valid_leads_saved: int
    invalid_or_duplicates_skipped: int
    details: List[str]
