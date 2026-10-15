"""
HubSpot CRM Integration Service
-------------------------------
Synchronizes lead profiles, updates engagement stages, and logs timeline notes.
Provides two-way data alignment between Converzia's autonomous SDR and the sales CRM.

SYSTEM DESIGN NOTE:
- Outbound sales platforms must never leave CRMs out of sync.
- All outreach events (email sent, reply received, meeting requested) are logged as CRM notes.
- Gracefully skips CRM calls if HUBSPOT_ACCESS_TOKEN is omitted.
"""

from typing import Optional, Dict, Any
import requests
from app.core.config import settings
from app.core.logger import logger


class HubSpotCRMService:
    """Manages contact upserting and note logging into HubSpot CRM."""

    def __init__(self):
        self.token = settings.HUBSPOT_ACCESS_TOKEN
        self.enabled = bool(self.token) and settings.HUBSPOT_ENABLED
        self.base_url = "https://api.hubapi.com/crm/v3/objects"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def upsert_contact(
        self,
        email: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        company: Optional[str] = None,
        website: Optional[str] = None
    ) -> Optional[str]:
        """
        Creates or updates a contact in HubSpot.
        Returns the HubSpot Contact ID or None.
        """
        if not self.enabled:
            return None

        url = f"{self.base_url}/contacts"
        properties = {
            "email": email,
            "firstname": first_name or "",
            "lastname": last_name or "",
            "company": company or "",
            "website": website or ""
        }

        try:
            resp = requests.post(url, headers=self.headers, json={"properties": properties}, timeout=10)
            if resp.status_code in (200, 201):
                contact_id = resp.json().get("id")
                logger.info(f"Created HubSpot contact {contact_id} for {email}")
                return contact_id

            if resp.status_code == 409:  # Contact already exists -> find and patch
                search_url = f"{self.base_url}/contacts/search"
                search_payload = {
                    "filterGroups": [{
                        "filters": [{"propertyName": "email", "operator": "EQ", "value": email}]
                    }]
                }
                search_resp = requests.post(search_url, headers=self.headers, json=search_payload, timeout=10)
                if search_resp.ok:
                    results = search_resp.json().get("results", [])
                    if results:
                        contact_id = results[0]["id"]
                        patch_url = f"{self.base_url}/contacts/{contact_id}"
                        requests.patch(patch_url, headers=self.headers, json={"properties": properties}, timeout=10)
                        logger.info(f"Updated existing HubSpot contact {contact_id} for {email}")
                        return contact_id

        except Exception as e:
            logger.warning(f"HubSpot contact sync failed for {email}: {e}")

        return None

    def log_activity_note(self, email: str, subject: str, content: str) -> bool:
        """Logs an outreach interaction or SDR reply note to the contact's CRM timeline."""
        if not self.enabled:
            return False

        try:
            search_url = f"{self.base_url}/contacts/search"
            search_payload = {
                "filterGroups": [{
                    "filters": [{"propertyName": "email", "operator": "EQ", "value": email}]
                }]
            }
            search_resp = requests.post(search_url, headers=self.headers, json=search_payload, timeout=10)
            if not search_resp.ok:
                return False

            results = search_resp.json().get("results", [])
            if not results:
                return False

            contact_id = results[0]["id"]
            note_url = f"{self.base_url}/notes"
            note_payload = {
                "properties": {
                    "hs_note_body": f"Outreach Activity: {subject}\n\n{content}"
                },
                "associations": [
                    {
                        "to": {"id": contact_id},
                        "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 202}]
                    }
                ]
            }
            note_resp = requests.post(note_url, headers=self.headers, json=note_payload, timeout=10)
            return note_resp.ok

        except Exception as e:
            logger.warning(f"HubSpot note creation failed for {email}: {e}")
            return False


crm_service = HubSpotCRMService()
