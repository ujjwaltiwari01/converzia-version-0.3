"""
Multi-Stage Cadence Sequencer Engine
------------------------------------
Executes automated, state-aware follow-up sequences across prospect cohorts:
- Step 1: Initial Cold Introduction (Curiosity Open-Loop)
- Step 2: Value-Add Follow-up (Case study / Benchmark data, triggered if opened or 2-day timeout)
- Step 3: Respectful Breakup (Closing the loop, triggered after 4 additional days)

SYSTEM DESIGN / SEQUENCING STATE MACHINE:
- Prevents double-emailing or emailing contacts who already replied/opted-out.
- Dynamic cadence branching: Checks if the prospect opened the previous email to calibrate follow-up tone.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.models import Lead, OutreachLog, Campaign
from app.pipeline.email_generator import email_generator
from app.pipeline.spam_checker import spam_checker
from app.services.email_dispatcher import dispatcher
from app.core.logger import logger


class SequenceEngine:
    """Orchestrates multi-stage email sequences with telemetry state awareness."""

    def evaluate_and_advance_lead(
        self,
        db: Session,
        lead: Lead,
        campaign: Optional[Campaign] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluates a lead's current outreach history and generates/dispatches
        the next sequence step if timing criteria are met.
        """
        # Guard: Never email unsubscribed or meeting-booked prospects
        if lead.status in ("OPT_OUT", "MEETING_SET", "UNSUBSCRIBE"):
            logger.info(f"Skipping sequence for lead {lead.email}: status is {lead.status}")
            return None

        # Fetch chronological outreach logs for this lead
        logs = db.query(OutreachLog).filter(
            OutreachLog.lead_id == lead.id
        ).order_by(OutreachLog.created_at.asc()).all()

        now = datetime.utcnow()

        # CASE 1: Lead has never received an email -> Step 1 (Initial Outreach)
        if not logs:
            logger.info(f"Lead {lead.email} ready for Step 1 Initial Outreach.")
            hook = ""
            if lead.brand_voice_summary and isinstance(lead.brand_voice_summary, dict):
                hook = lead.brand_voice_summary.get("personalized_hook", "")

            email_data = email_generator.generate_initial_email(
                company_name=lead.company_name or "your team",
                website_url=lead.website_url or "",
                recipient_name=lead.first_name,
                primary_offering=lead.scraped_title or "B2B Services",
                personalized_hook=hook,
                keywords=lead.keywords or ""
            )

            # Check spam score
            spam_res = spam_checker.analyze(email_data["subject"], email_data["body"])

            # Create DB Log
            new_log = OutreachLog(
                lead_id=lead.id,
                campaign_id=campaign.id if campaign else None,
                sequence_step=1,
                subject=email_data["subject"],
                body=email_data["body"],
                spam_score=spam_res["spam_score"],
                status="SENT",
                sent_at=now
            )
            db.add(new_log)
            db.flush()

            # Dispatch with tracking token
            dispatch_res = dispatcher.send(
                to_email=lead.email,
                to_name=lead.first_name,
                subject=new_log.subject,
                body=new_log.body,
                tracking_token=new_log.tracking_token
            )

            lead.status = "IN_SEQUENCE"
            db.commit()

            return {
                "step": 1,
                "lead_email": lead.email,
                "subject": new_log.subject,
                "tracking_token": new_log.tracking_token,
                "status": "DISPATCHED"
            }

        last_log = logs[-1]

        # Guard: If lead replied to the last email, sequence is complete/paused for human/agent review
        if last_log.status == "REPLIED" or last_log.replied_at is not None:
            logger.info(f"Lead {lead.email} already replied. Sequence paused.")
            return None

        # CASE 2: Lead received Step 1 -> Check if 2 days passed -> Step 2
        last_sent = last_log.sent_at or last_log.created_at
        time_elapsed = now - last_sent

        if last_log.sequence_step == 1:
            # 2 days delay for follow-up (can be accelerated for demo)
            if time_elapsed >= timedelta(days=2) or last_log.open_count > 0:
                logger.info(f"Triggering Step 2 Value-Add Follow-up for {lead.email}")
                followup_data = email_generator.generate_followup_email(
                    company_name=lead.company_name or "your team",
                    prev_subject=last_log.subject,
                    prev_body=last_log.body,
                    sequence_step=2,
                    recipient_name=lead.first_name
                )
                spam_res = spam_checker.analyze(followup_data["subject"], followup_data["body"])

                new_log = OutreachLog(
                    lead_id=lead.id,
                    campaign_id=campaign.id if campaign else None,
                    sequence_step=2,
                    subject=followup_data["subject"],
                    body=followup_data["body"],
                    spam_score=spam_res["spam_score"],
                    status="SENT",
                    sent_at=now
                )
                db.add(new_log)
                db.flush()

                dispatcher.send(
                    to_email=lead.email,
                    to_name=lead.first_name,
                    subject=new_log.subject,
                    body=new_log.body,
                    tracking_token=new_log.tracking_token
                )
                db.commit()

                return {
                    "step": 2,
                    "lead_email": lead.email,
                    "subject": new_log.subject,
                    "status": "DISPATCHED"
                }

        # CASE 3: Lead received Step 2 -> Check if 4 days passed -> Step 3 Breakup
        elif last_log.sequence_step == 2:
            if time_elapsed >= timedelta(days=4):
                logger.info(f"Triggering Step 3 Breakup email for {lead.email}")
                breakup_data = email_generator.generate_followup_email(
                    company_name=lead.company_name or "your team",
                    prev_subject=last_log.subject,
                    prev_body=last_log.body,
                    sequence_step=3,
                    recipient_name=lead.first_name
                )
                spam_res = spam_checker.analyze(breakup_data["subject"], breakup_data["body"])

                new_log = OutreachLog(
                    lead_id=lead.id,
                    campaign_id=campaign.id if campaign else None,
                    sequence_step=3,
                    subject=breakup_data["subject"],
                    body=breakup_data["body"],
                    spam_score=spam_res["spam_score"],
                    status="SENT",
                    sent_at=now
                )
                db.add(new_log)
                db.flush()

                dispatcher.send(
                    to_email=lead.email,
                    to_name=lead.first_name,
                    subject=new_log.subject,
                    body=new_log.body,
                    tracking_token=new_log.tracking_token
                )
                lead.status = "SEQUENCE_COMPLETED"
                db.commit()

                return {
                    "step": 3,
                    "lead_email": lead.email,
                    "subject": new_log.subject,
                    "status": "DISPATCHED"
                }

        return None


sequencer = SequenceEngine()
