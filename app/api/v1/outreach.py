"""
Outreach Generation & Dispatch API Router
-----------------------------------------
Provides endpoints to preview generated emails, evaluate deliverability risk,
and dispatch individual outreach emails.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Lead, OutreachLog
from app.schemas.outreach import (
    GenerateEmailRequest, EmailPreviewResponse, SendEmailRequest, SendEmailResponse
)
from app.services.scraper import scraper
from app.pipeline.brand_voice import brand_voice_pipeline
from app.pipeline.email_generator import email_generator
from app.pipeline.spam_checker import spam_checker
from app.services.email_dispatcher import dispatcher
from app.services.crm_sync import crm_service

router = APIRouter(prefix="/outreach", tags=["Outreach"])


@router.post("/generate", response_model=EmailPreviewResponse)
def generate_email_preview(req: GenerateEmailRequest, db: Session = Depends(get_db)):
    """
    Generates a personalized cold email or follow-up with A/B subject line variants,
    personalization hook, and real-time spam deliverability score.
    """
    company = req.company_name or ""
    website = req.website_url or ""
    recipient = req.recipient_name or ""
    keywords = req.keywords or ""
    hook = ""

    # If lead_id is provided, fetch stored data
    if req.lead_id:
        lead = db.query(Lead).filter(Lead.id == req.lead_id).first()
        if lead:
            company = lead.company_name or company
            website = lead.website_url or website
            recipient = lead.first_name or recipient
            keywords = lead.keywords or keywords
            if lead.brand_voice_summary and isinstance(lead.brand_voice_summary, dict):
                hook = lead.brand_voice_summary.get("personalized_hook", "")

    # If website provided but not yet scraped, run quick scrape & brand voice extraction
    if website and not hook:
        scraped = scraper.scrape(website)
        brand = brand_voice_pipeline.analyze(
            company_name=company,
            website_url=website,
            scraped_title=scraped.get("title", ""),
            scraped_meta_desc=scraped.get("meta_description", ""),
            scraped_headings=scraped.get("headings", []),
            scraped_content=scraped.get("body_snippet", "")
        )
        hook = brand.get("personalized_hook", "")

    # Generate cold email or follow-up
    if req.sequence_step == 1:
        email_data = email_generator.generate_initial_email(
            company_name=company or "your team",
            website_url=website,
            recipient_name=recipient,
            personalized_hook=hook,
            keywords=keywords
        )
    else:
        email_data = email_generator.generate_followup_email(
            company_name=company or "your team",
            prev_subject=req.prev_subject or f"micro-idea for {company}",
            prev_body=req.prev_body or "",
            sequence_step=req.sequence_step,
            recipient_name=recipient
        )

    # Deliverability pre-check
    spam_res = spam_checker.analyze(email_data["subject"], email_data["body"])

    return EmailPreviewResponse(
        subject=email_data["subject"],
        body=email_data["body"],
        alternative_subjects=email_data.get("alternative_subjects", []),
        spam_score=spam_res["spam_score"],
        spam_reasons=spam_res.get("reasons", []),
        personalization_hook=email_data.get("personalization_hook", hook),
        target_company=company or "Target Company"
    )


@router.post("/send", response_model=SendEmailResponse)
def send_email(req: SendEmailRequest, db: Session = Depends(get_db)):
    """Dispatches an email to a lead with tracking instrumentation and database logging."""
    lead = db.query(Lead).filter(Lead.id == req.lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Evaluate deliverability
    spam_res = spam_checker.analyze(req.subject, req.body)

    # Create Outreach Log
    log = OutreachLog(
        lead_id=lead.id,
        campaign_id=req.campaign_id,
        sequence_step=req.sequence_step,
        subject=req.subject,
        body=req.body,
        spam_score=spam_res["spam_score"],
        status="SENT",
        sent_at=datetime.utcnow()
    )
    db.add(log)
    db.flush()

    # Dispatch email
    dispatch_res = dispatcher.send(
        to_email=lead.email,
        to_name=lead.first_name,
        subject=log.subject,
        body=log.body,
        tracking_token=log.tracking_token
    )

    lead.status = "IN_SEQUENCE"
    db.commit()

    # Async CRM sync (non-blocking)
    crm_service.upsert_contact(
        email=lead.email,
        first_name=lead.first_name,
        company=lead.company_name,
        website=lead.website_url
    )
    crm_service.log_activity_note(
        email=lead.email,
        subject=log.subject,
        content=log.body
    )

    return SendEmailResponse(
        outreach_log_id=log.id,
        recipient_email=lead.email,
        status="SENT",
        tracking_token=log.tracking_token,
        message="Email successfully dispatched with tracking pixel and click wrapper"
    )
