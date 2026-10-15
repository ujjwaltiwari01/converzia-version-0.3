"""
FastAPI Master Router
---------------------
Aggregates and mounts all version 1 endpoints:
- /leads: Lead ingestion, CSV bulk upload, and enrichment
- /campaigns: Multi-stage cadences and campaign limits
- /outreach: AI email synthesis, A/B testing, and dispatch
- /sdr: Autonomous SDR agent reasoning, objection handling, and batch runs
- /tracking: 1x1 open pixel and click redirect telemetry
- /analytics: Executive metrics and benchmark comparisons
"""

from fastapi import APIRouter
from app.api.v1.leads import router as leads_router
from app.api.v1.campaigns import router as campaigns_router
from app.api.v1.outreach import router as outreach_router
from app.api.v1.sdr import router as sdr_router
from app.api.v1.tracking import router as tracking_router
from app.api.v1.analytics import router as analytics_router

api_router = APIRouter()

api_router.include_router(leads_router)
api_router.include_router(campaigns_router)
api_router.include_router(outreach_router)
api_router.include_router(sdr_router)
api_router.include_router(tracking_router)
api_router.include_router(analytics_router)
