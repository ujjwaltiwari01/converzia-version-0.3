"""
Campaigns & Cadence API Router
------------------------------
Manages outbound campaigns, multi-stage cadence configurations, and performance metrics.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.db.models import Campaign, SequenceStep, OutreachLog, Lead
from app.schemas.campaign import (
    CampaignCreate, CampaignResponse, CampaignMetricsResponse
)

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


@router.post("/", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
def create_campaign(campaign_in: CampaignCreate, db: Session = Depends(get_db)):
    """Creates a new B2B outreach campaign with default 3-stage SDR sequences."""
    new_campaign = Campaign(
        name=campaign_in.name,
        description=campaign_in.description,
        target_icp=campaign_in.target_icp,
        value_proposition=campaign_in.value_proposition,
        daily_lead_limit=campaign_in.daily_lead_limit,
        status="ACTIVE"
    )
    db.add(new_campaign)
    db.flush()

    # If sequences provided, use them; otherwise populate standard 3-stage cadence
    if campaign_in.sequences:
        for seq in campaign_in.sequences:
            step = SequenceStep(
                campaign_id=new_campaign.id,
                step_number=seq.step_number,
                delay_days=seq.delay_days,
                step_type=seq.step_type,
                prompt_focus=seq.prompt_focus
            )
            db.add(step)
    else:
        # Standard High-Conversion Cadence
        db.add(SequenceStep(
            campaign_id=new_campaign.id,
            step_number=1,
            delay_days=0,
            step_type="INITIAL",
            prompt_focus="Curiosity open loop & website brand hook"
        ))
        db.add(SequenceStep(
            campaign_id=new_campaign.id,
            step_number=2,
            delay_days=2,
            step_type="FOLLOWUP_OPENED",
            prompt_focus="Social proof, benchmark data, and 60-second video offer"
        ))
        db.add(SequenceStep(
            campaign_id=new_campaign.id,
            step_number=3,
            delay_days=4,
            step_type="BREAKUP",
            prompt_focus="Respectful breakup email closing the loop"
        ))

    db.commit()
    db.refresh(new_campaign)
    return new_campaign


@router.get("/", response_model=List[CampaignResponse])
def list_campaigns(db: Session = Depends(get_db)):
    """Lists all outreach campaigns."""
    return db.query(Campaign).all()


@router.get("/{campaign_id}", response_model=CampaignResponse)
def get_campaign(campaign_id: int, db: Session = Depends(get_db)):
    """Gets details and sequence steps for a specific campaign."""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.get("/{campaign_id}/metrics", response_model=CampaignMetricsResponse)
def get_campaign_metrics(campaign_id: int, db: Session = Depends(get_db)):
    """
    Computes real-time engagement telemetry:
    Open rates, click rates, reply rates, and benchmark comparisons.
    """
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    logs = db.query(OutreachLog).filter(OutreachLog.campaign_id == campaign_id).all()
    sent_count = len(logs)
    opened_count = sum(1 for log in logs if log.open_count > 0 or log.opened_at is not None)
    clicked_count = sum(1 for log in logs if log.click_count > 0 or log.clicked_at is not None)
    replied_count = sum(1 for log in logs if log.status == "REPLIED" or log.replied_at is not None)

    open_rate = round((opened_count / sent_count * 100), 1) if sent_count > 0 else 0.0
    click_rate = round((clicked_count / sent_count * 100), 1) if sent_count > 0 else 0.0
    reply_rate = round((replied_count / sent_count * 100), 1) if sent_count > 0 else 0.0

    # Benchmark comparison note
    if open_rate >= 50.0:
        comp = f"Outperforming: {open_rate}% vs 15-25% industry baseline (+{(open_rate - 20):.1f}% lift)"
    else:
        comp = f"Currently at {open_rate}%. Target 50-70% achievable as personalization hooks calibrate."

    return CampaignMetricsResponse(
        campaign_id=campaign_id,
        total_leads=db.query(Lead).count(),
        emails_sent=sent_count,
        emails_opened=opened_count,
        emails_clicked=clicked_count,
        emails_replied=replied_count,
        open_rate_percent=open_rate,
        click_rate_percent=click_rate,
        reply_rate_percent=reply_rate,
        benchmark_comparison=comp
    )
