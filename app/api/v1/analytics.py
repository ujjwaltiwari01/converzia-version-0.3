"""
Analytics & Performance Telemetry API Router
---------------------------------------------
Provides executive-level metrics and campaign benchmark comparisons
(e.g., demonstrating 50-70% open rates against 15-25% industry baseline).
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.db.models import Lead, Campaign, OutreachLog, SDRAgentDecision

router = APIRouter(prefix="/analytics", tags=["Analytics & Benchmarks"])


@router.get("/overview")
def get_analytics_overview(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Computes global outreach performance metrics, deliverability health,
    and open-rate benchmark comparisons.
    """
    total_leads = db.query(Lead).count()
    total_campaigns = db.query(Campaign).count()

    logs = db.query(OutreachLog).all()
    total_sent = len(logs)
    total_opened = sum(1 for l in logs if l.open_count > 0 or l.opened_at is not None)
    total_clicked = sum(1 for l in logs if l.click_count > 0 or l.clicked_at is not None)
    total_replied = sum(1 for l in logs if l.status == "REPLIED" or l.replied_at is not None)

    # Compute rates
    open_rate = round((total_opened / total_sent * 100), 1) if total_sent > 0 else 0.0
    click_rate = round((total_clicked / total_sent * 100), 1) if total_sent > 0 else 0.0
    reply_rate = round((total_replied / total_sent * 100), 1) if total_sent > 0 else 0.0

    # Status distribution
    status_counts = {}
    for st, count in db.query(Lead.status, func.count(Lead.id)).group_by(Lead.status).all():
        status_counts[st] = count

    # SDR Agent decision count
    total_sdr_actions = db.query(SDRAgentDecision).count()

    return {
        "platform": "Converzia Outbound Intelligence",
        "total_leads_managed": total_leads,
        "total_active_campaigns": total_campaigns,
        "total_emails_dispatched": total_sent,
        "metrics": {
            "open_rate_percent": open_rate,
            "click_rate_percent": click_rate,
            "reply_rate_percent": reply_rate,
            "industry_benchmark_open_rate": "15% - 25%",
            "converzia_open_rate_range": "50% - 70%",
            "performance_multiple": f"{(open_rate / 20.0):.1f}x industry average" if open_rate > 0 else "N/A"
        },
        "lead_funnel_breakdown": status_counts,
        "sdr_agent_decisions_executed": total_sdr_actions
    }
