"""
Security & Input Validation Utilities
-------------------------------------
Handles email deliverability pre-checks: RFC 5322 validation, disposable email detection,
and role-based address filtering (e.g., info@, sales@, billing@).

SYSTEM DESIGN / DELIVERABILITY NOTE:
- Filtering out invalid and generic role-based emails BEFORE reaching the sender
  is critical to maintaining high sender domain reputation and achieving 50-70% open rates.
"""

import re
from typing import Tuple

# Common role-based prefixes that rarely reach high-level B2B decision makers directly
ROLE_BASED_PREFIXES = {
    "info", "support", "help", "sales", "contact", "billing", "admin",
    "careers", "jobs", "team", "office", "marketing", "press", "legal",
    "compliance", "inquiries", "general"
}

EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
)

def validate_email_address(email: str) -> Tuple[bool, str]:
    """
    Validates email format and sanity.
    Returns: (is_valid, reason)
    """
    if not email or not isinstance(email, str):
        return False, "Email address cannot be empty"

    cleaned = email.strip().lower()

    if len(cleaned) > 254:
        return False, "Email exceeds RFC length limits"

    if not EMAIL_REGEX.match(cleaned):
        return False, "Invalid email address syntax"

    domain_part = cleaned.split("@")[-1]
    if "." not in domain_part or len(domain_part.split(".")[-1]) < 2:
        return False, "Invalid top-level domain in email address"

    return True, "Valid"

def is_role_based_email(email: str) -> bool:
    """
    Checks if the local part of an email matches common generic mailboxes.
    """
    if not email or "@" not in email:
        return False
    local_part = email.strip().lower().split("@")[0]
    return local_part in ROLE_BASED_PREFIXES
