"""
Telemetry & Engagement Tracking Router
--------------------------------------
Serves the 1x1 transparent open-tracking pixel and click-tracking redirect gateway.
Powers Converzia's real-time telemetry to measure 50-70% campaign open rates.

SYSTEM DESIGN NOTE:
- Sub-millisecond response time: Open pixel must return instantly without blocking the email client.
- Cache-Control: Set to `no-cache, no-store, must-revalidate` so email clients don't cache the pixel
  and suppress repeated open telemetry.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import OutreachLog, Lead
from app.core.logger import logger

router = APIRouter(prefix="/tracking", tags=["Telemetry & Tracking"])

# Pre-computed 1x1 transparent PNG byte sequence
TRANSPARENT_1X1_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00"
    b"\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


@router.get("/pixel/{token_with_ext}")
def track_open_pixel(token_with_ext: str, db: Session = Depends(get_db)):
    """
    Receives request when an email is opened.
    Updates the open timestamp, increments open count, and returns a 1x1 transparent PNG.
    """
    token = token_with_ext.replace(".png", "")
    log = db.query(OutreachLog).filter(OutreachLog.tracking_token == token).first()

    if log:
        now = datetime.utcnow()
        if not log.opened_at:
            log.opened_at = now
            log.status = "OPENED"
        log.open_count += 1
        db.commit()
        logger.info(f"Open event tracked for email log #{log.id} (Total opens: {log.open_count})")

    headers = {
        "Content-Type": "image/png",
        "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
        "Pragma": "no-cache",
        "Expires": "0"
    }
    return Response(content=TRANSPARENT_1X1_PNG, media_type="image/png", headers=headers)


@router.get("/click")
def track_click_and_redirect(
    token: str = Query(..., description="Tracking token from email"),
    target: str = Query(..., description="Destination destination URL"),
    db: Session = Depends(get_db)
):
    """
    Receives click event from an instrumented hyperlink, records telemetry,
    and immediately redirects the prospect to their target URL.
    """
    log = db.query(OutreachLog).filter(OutreachLog.tracking_token == token).first()
    if log:
        now = datetime.utcnow()
        if not log.clicked_at:
            log.clicked_at = now
            if log.status != "REPLIED":
                log.status = "CLICKED"
        log.click_count += 1
        db.commit()
        logger.info(f"Click event recorded for email log #{log.id} -> {target}")

    # Fallback safe URL if target is malformed
    clean_target = target if target.startswith(("http://", "https://")) else "https://" + target
    return RedirectResponse(url=clean_target, status_code=status.HTTP_302_FOUND)
