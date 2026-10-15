"""
Autonomous SDR Agent API Router
-------------------------------
Endpoints for autonomous prospect reply classification, objection handling,
and executing scalable batch outreach runs (up to 1,000 leads/day).
"""

import time
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Lead, SDRAgentDecision, OutreachLog
from app.schemas.agent import (
    SDRClassifyRequest, SDRDecisionResponse, BatchSDRRunRequest, BatchSDRRunResponse
)
from app.agents.sdr_agent import sdr_agent
from app.workers.batch_processor import batch_processor
from app.services.crm_sync import crm_service

router = APIRouter(prefix="/sdr", tags=["Autonomous SDR Agent"])


@router.post("/classify-reply", response_model=SDRDecisionResponse)
def classify_prospect_reply(req: SDRClassifyRequest, db: Session = Depends(get_db)):
    """
    Simulates or handles an incoming prospect email reply.
    The Autonomous SDR Agent:
    1. Reads reply text and historical context.
    2. Classifies buyer intent (Meeting, Objection, OOF, Unsubscribe).
    3. Drafts personalized objection response or calendar link.
    4. Logs decision in database and updates CRM.
    """
    lead = db.query(Lead).filter(Lead.id == req.lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Run Autonomous SDR Agent evaluation
    decision = sdr_agent.evaluate_reply(
        reply_text=req.prospect_reply_text,
        company_name=lead.company_name or "the prospect",
        lead_id=lead.id
    )

    # Persist decision log in PostgreSQL
    db_decision = SDRAgentDecision(
        lead_id=lead.id,
        prospect_input_event="REPLY_RECEIVED",
        prospect_reply_text=req.prospect_reply_text,
        classification=decision["classification"],
        confidence_score=decision.get("confidence_score", 0.9),
        reasoning=decision.get("reasoning", ""),
        recommended_action=decision.get("recommended_action", ""),
        generated_response=decision.get("suggested_reply"),
        is_executed=True
    )
    db.add(db_decision)

    # State Transition
    classification = decision["classification"]
    if classification == "MEETING_REQUESTED":
        lead.status = "MEETING_SET"
    elif classification == "UNSUBSCRIBE":
        lead.status = "OPT_OUT"
    else:
        lead.status = "REPLIED"

    db.commit()

    # Sync note with CRM
    crm_service.log_activity_note(
        email=lead.email,
        subject=f"Prospect Reply: {classification}",
        content=f"Reply: {req.prospect_reply_text}\n\nAgent Action: {decision.get('recommended_action')}\nResponse: {decision.get('suggested_reply')}"
    )

    return SDRDecisionResponse(
        lead_id=lead.id,
        classification=decision["classification"],
        confidence_score=decision.get("confidence_score", 0.9),
        reasoning=decision.get("reasoning", ""),
        recommended_action=decision.get("recommended_action", ""),
        suggested_reply=decision.get("suggested_reply"),
        next_sequence_step=None,
        delay_hours_before_send=decision.get("delay_hours", 0)
    )


@router.post("/batch-run", response_model=BatchSDRRunResponse)
async def run_batch_outreach(req: BatchSDRRunRequest, db: Session = Depends(get_db)):
    """
    Executes scalable async lead processing (up to 1,000 leads/day).
    Enriches unscraped leads, evaluates cadence state, and dispatches sequences.
    """
    start_time = time.time()

    query = db.query(Lead).filter(Lead.status.in_(["NEW", "ENRICHED", "IN_SEQUENCE"]))
    leads = query.limit(req.max_leads_to_process).all()

    if not leads:
        return BatchSDRRunResponse(
            total_processed=0,
            emails_generated=0,
            emails_dispatched=0,
            skipped_or_paused=0,
            execution_time_seconds=0.0,
            summary=["No eligible leads found for batch outreach."]
        )

    lead_ids = [l.id for l in leads]
    results = await batch_processor.run_batch(lead_ids, dry_run=req.dry_run)

    dispatched = sum(1 for r in results if r.get("status") == "DISPATCHED")
    generated = sum(1 for r in results if r.get("status") in ("DISPATCHED", "ENRICHED_DRY_RUN"))
    skipped = len(results) - dispatched

    duration = round(time.time() - start_time, 2)
    summary_lines = [
        f"Processed {len(lead_ids)} leads in {duration}s.",
        f"Dry run mode: {req.dry_run}.",
        f"Successfully generated: {generated}, Dispatched: {dispatched}, Skipped/Paused: {skipped}."
    ]

    return BatchSDRRunResponse(
        total_processed=len(lead_ids),
        emails_generated=generated,
        emails_dispatched=dispatched,
        skipped_or_paused=skipped,
        execution_time_seconds=duration,
        summary=summary_lines
    )
