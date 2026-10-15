"""
Leads API Router
----------------
Provides endpoints for lead ingestion, CSV batch importing, manual enrichment,
and profile management.
"""

import io
import csv
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Lead
from app.schemas.lead import (
    LeadCreate, LeadResponse, LeadUpdate, LeadBatchUploadResponse
)
from app.core.security import validate_email_address, is_role_based_email
from app.services.scraper import scraper
from app.pipeline.brand_voice import brand_voice_pipeline
from app.core.logger import logger

router = APIRouter(prefix="/leads", tags=["Leads"])


@router.post("/", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
def create_lead(lead_in: LeadCreate, db: Session = Depends(get_db)):
    """Creates a new prospect lead with automated email deliverability validation."""
    is_valid, reason = validate_email_address(str(lead_in.email))
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Invalid email: {reason}")

    # Check duplicate
    existing = db.query(Lead).filter(Lead.email == lead_in.email).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Lead with email {lead_in.email} already exists")

    new_lead = Lead(
        email=str(lead_in.email).strip().lower(),
        first_name=lead_in.first_name,
        last_name=lead_in.last_name,
        company_name=lead_in.company_name,
        website_url=str(lead_in.website_url) if lead_in.website_url else None,
        industry=lead_in.industry,
        keywords=lead_in.keywords,
        status="NEW"
    )
    db.add(new_lead)
    db.commit()
    db.refresh(new_lead)
    return new_lead


@router.get("/", response_model=List[LeadResponse])
def list_leads(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db)
):
    """Lists leads with pagination and optional status filter."""
    query = db.query(Lead)
    if status_filter:
        query = query.filter(Lead.status == status_filter)
    return query.offset(skip).limit(limit).all()


@router.get("/{lead_id}", response_model=LeadResponse)
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    """Retrieves full profile of a lead including scraped data and brand voice."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.post("/{lead_id}/enrich", response_model=LeadResponse)
def enrich_lead(lead_id: int, db: Session = Depends(get_db)):
    """
    Triggers on-demand website scraping and LangChain brand voice extraction
    for an individual lead.
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if not lead.website_url:
        raise HTTPException(status_code=400, detail="Lead does not have a website URL to enrich")

    # Scrape website
    scrape_data = scraper.scrape(lead.website_url)
    lead.scraped_title = scrape_data.get("title", "")
    lead.scraped_meta_desc = scrape_data.get("meta_description", "")
    lead.scraped_summary = scrape_data.get("body_snippet", "")

    # LangChain Brand Voice Analysis
    brand_profile = brand_voice_pipeline.analyze(
        company_name=lead.company_name or "the company",
        website_url=lead.website_url,
        scraped_title=lead.scraped_title,
        scraped_meta_desc=lead.scraped_meta_desc,
        scraped_headings=scrape_data.get("headings", []),
        scraped_content=lead.scraped_summary
    )
    lead.brand_voice_summary = brand_profile
    lead.status = "ENRICHED"
    db.commit()
    db.refresh(lead)

    return lead


@router.post("/upload-csv", response_model=LeadBatchUploadResponse)
async def upload_leads_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Bulk uploads leads from a CSV file.
    Validates email format, sanitizes inputs, and skips duplicates.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a CSV")

    contents = await file.read()
    decoded = contents.decode("utf-8", errors="ignore")
    reader = csv.DictReader(io.StringIO(decoded))

    total = 0
    saved = 0
    skipped = 0
    details = []

    for row in reader:
        total += 1
        # Extract email using common CSV column names
        email = (row.get("email") or row.get("Email") or row.get("contact_email") or "").strip().lower()
        if not email:
            skipped += 1
            details.append(f"Row {total}: Missing email")
            continue

        is_valid, reason = validate_email_address(email)
        if not is_valid:
            skipped += 1
            details.append(f"Row {total} ({email}): {reason}")
            continue

        existing = db.query(Lead).filter(Lead.email == email).first()
        if existing:
            skipped += 1
            details.append(f"Row {total} ({email}): Duplicate email skipped")
            continue

        company = (row.get("company") or row.get("co_name") or row.get("Company") or "").strip()
        website = (row.get("website") or row.get("Website") or "").strip()
        name = (row.get("name") or row.get("Name") or "").strip()
        keywords = (row.get("keywords") or row.get("Keywords") or "").strip()

        first_name = name.split()[0] if name else None
        last_name = " ".join(name.split()[1:]) if name and len(name.split()) > 1 else None

        new_lead = Lead(
            email=email,
            first_name=first_name,
            last_name=last_name,
            company_name=company or None,
            website_url=website or None,
            keywords=keywords or None,
            status="NEW"
        )
        db.add(new_lead)
        saved += 1

    db.commit()
    return LeadBatchUploadResponse(
        total_received=total,
        valid_leads_saved=saved,
        invalid_or_duplicates_skipped=skipped,
        details=details[:20]  # Return first 20 skip notes
    )
