"""
Scalable Async Batch Outreach Worker
------------------------------------
Executes high-throughput enrichment and outreach batches:
Capable of processing up to 1,000 leads/day with concurrency controls and rate limiting.

SYSTEM DESIGN / 1,000 LEADS/DAY ARCHITECTURE:
- High-volume outbound requires balancing three competing constraints:
  1. Web scraping network latency (I/O bound).
  2. LLM token rate limits (OpenAI TPM/RPM bounds).
  3. ESP email dispatch pacing (preventing sender domain blacklisting).
- Solution:
  - Semaphore concurrency bounding (default: 10 concurrent prospect workers).
  - Caching scraped intelligence in PostgreSQL so prospects are never rescraped.
  - Asynchronous non-blocking task queue with checkpointing and error isolation.
"""

import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import Lead, Campaign
from app.services.scraper import scraper
from app.pipeline.brand_voice import brand_voice_pipeline
from app.pipeline.email_generator import email_generator
from app.pipeline.spam_checker import spam_checker
from app.services.email_dispatcher import dispatcher
from app.agents.sequencer import sequencer
from app.core.logger import logger


class BatchOutreachProcessor:
    """Manages concurrent enrichment and automated outreach for lead cohorts."""

    def __init__(self, concurrency_limit: int = 10):
        self.semaphore = asyncio.Semaphore(concurrency_limit)

    async def enrich_and_outreach_lead(
        self,
        lead_id: int,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Processes a single lead through the entire intelligence pipeline:
        Scraping -> Brand Voice Analysis -> Sequence Generation -> Dispatch.
        """
        async with self.semaphore:
            # Run blocking database and network operations in threadpool
            return await asyncio.to_thread(self._sync_process_lead, lead_id, dry_run)

    def _sync_process_lead(self, lead_id: int, dry_run: bool) -> Dict[str, Any]:
        db: Session = SessionLocal()
        try:
            lead = db.query(Lead).filter(Lead.id == lead_id).first()
            if not lead:
                return {"lead_id": lead_id, "status": "NOT_FOUND"}

            # Step 1: Scrape Website if not previously cached
            if not lead.scraped_title and lead.website_url:
                scrape_res = scraper.scrape(lead.website_url)
                lead.scraped_title = scrape_res.get("title", "")
                lead.scraped_meta_desc = scrape_res.get("meta_description", "")
                lead.scraped_summary = scrape_res.get("body_snippet", "")
                lead.scraped_at = datetime.utcnow()
                db.commit()

            # Step 2: Extract Brand Voice & ICP Profile if missing
            if not lead.brand_voice_summary:
                brand_profile = brand_voice_pipeline.analyze(
                    company_name=lead.company_name or "the company",
                    website_url=lead.website_url or "",
                    scraped_title=lead.scraped_title or "",
                    scraped_meta_desc=lead.scraped_meta_desc or "",
                    scraped_content=lead.scraped_summary or ""
                )
                lead.brand_voice_summary = brand_profile
                lead.status = "ENRICHED"
                db.commit()

            # Step 3: Advance sequence / dispatch initial email if not dry_run
            if dry_run:
                return {
                    "lead_id": lead.id,
                    "email": lead.email,
                    "company": lead.company_name,
                    "status": "ENRICHED_DRY_RUN",
                    "hook": lead.brand_voice_summary.get("personalized_hook")
                }

            result = sequencer.evaluate_and_advance_lead(db, lead)
            return {
                "lead_id": lead.id,
                "email": lead.email,
                "status": "DISPATCHED" if result else "SKIPPED_OR_UP_TO_DATE",
                "details": result
            }

        except Exception as e:
            logger.error(f"Error processing lead {lead_id}: {e}")
            return {"lead_id": lead_id, "status": "ERROR", "error": str(e)}
        finally:
            db.close()

    async def run_batch(
        self,
        lead_ids: List[int],
        dry_run: bool = False
    ) -> List[Dict[str, Any]]:
        """Executes the batch processing pipeline asynchronously across all lead IDs."""
        tasks = [self.enrich_and_outreach_lead(lid, dry_run=dry_run) for lid in lead_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r if isinstance(r, dict) else {"error": str(r)} for r in results]


batch_processor = BatchOutreachProcessor(concurrency_limit=10)
