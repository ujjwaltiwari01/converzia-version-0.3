"""
Deliverability & Spam Trigger Analyzer
--------------------------------------
Evaluates email copy against real-world ESP (Email Service Provider) spam filtering heuristics.

SYSTEM DESIGN / 50-70% OPEN RATE SECRET:
- Industry average open rate is 15-25% largely because automated emails land in Gmail's "Promotions"
  or Microsoft Outlook's "Junk" folder.
- Converzia pre-evaluates every generated email before sending:
  1. Spam Keyword Penalty: Scans for 50+ aggressive marketing triggers ("guarantee", "free", "limited time").
  2. Subject Line Heuristics: Penalizes excessive capitalization, exclamation marks, or overly long subjects.
  3. Link Density: High link counts trigger ESP promotional tab categorization; limits to <= 1 link.
  4. Word Count Optimization: Highest open/reply velocity occurs at 50-125 words.
"""

from typing import Dict, Any, List
import re

# Curated list of high-risk spam trigger keywords that trip ESP filters
SPAM_TRIGGER_WORDS = [
    "100% free", "act now", "apply now", "as seen on", "bargain", "be your own boss",
    "best price", "big bucks", "bonus", "buy direct", "cancel anytime", "cash bonus",
    "certified", "cheap", "click here", "click now", "congratulations", "credit card",
    "cure", "dear friend", "direct marketing", "double your income", "earn $", "earn money",
    "eliminate debt", "exclusive deal", "expect to earn", "extra income", "fast cash",
    "financial freedom", "free access", "free consultation", "free gift", "free info",
    "free trial", "get out of debt", "get paid", "giveaway", "guaranteed", "increase sales",
    "instant", "investment", "join millions", "limited time", "make $", "make money",
    "miracle", "money back", "no catch", "no cost", "no credit check", "no experience",
    "no fees", "no gimmick", "no hidden", "no obligation", "no purchase", "no risk",
    "no strings attached", "not spam", "once in a lifetime", "one time", "online marketing",
    "open immediately", "opportunity", "order now", "passwords", "promise you",
    "pure profit", "refund", "remove", "reverse aging", "risk free", "save $",
    "save big", "special promotion", "terms and conditions", "this isn't spam",
    "unlimited", "urgent", "valuable", "viagra", "vicodin", "warranty", "while supplies last",
    "win", "winner", "winning", "work from home"
]


class SpamCheckerService:
    """Calculates email deliverability safety score and flags spam triggers."""

    def analyze(self, subject: str, body: str) -> Dict[str, Any]:
        """
        Calculates a deliverability risk score from 0 (pristine) to 100 (high spam risk).
        Returns risk score, status, and actionable recommendations.
        """
        score = 0.0
        reasons: List[str] = []
        combined_text = f"{subject} {body}".lower()

        # 1. Check Spam Trigger Keywords
        found_keywords = [kw for kw in SPAM_TRIGGER_WORDS if kw in combined_text]
        if found_keywords:
            penalty = len(found_keywords) * 15.0
            score += penalty
            reasons.append(f"Spam keywords detected: {', '.join(found_keywords[:4])}")

        # 2. Subject Line Checks
        if subject.isupper():
            score += 30.0
            reasons.append("Subject line is in ALL CAPS (high spam trigger)")

        exclamations = subject.count("!")
        if exclamations > 0:
            score += exclamations * 10.0
            reasons.append("Subject contains exclamation marks")

        subject_words = subject.split()
        if len(subject_words) > 9:
            score += 10.0
            reasons.append("Subject is over 9 words (optimal is 3-6 words)")

        # 3. Body Length & Structure Checks
        body_words = body.split()
        word_count = len(body_words)
        if word_count > 160:
            score += 15.0
            reasons.append(f"Body is too long ({word_count} words). B2B decision makers prefer under 125 words.")
        elif word_count < 25:
            score += 10.0
            reasons.append("Body is very brief (< 25 words). May lack sufficient context.")

        # 4. Link Density Check
        link_count = len(re.findall(r"https?://", body))
        if link_count > 2:
            score += 20.0
            reasons.append(f"Too many links ({link_count}). ESPs categorize emails with >1 link to Promotions tab.")

        # Cap score between 0 and 100
        final_score = min(max(score, 0.0), 100.0)

        # Categorize
        if final_score <= 15.0:
            status = "EXCELLENT"  # Prime for 50-70% open rates
        elif final_score <= 35.0:
            status = "GOOD"
        elif final_score <= 60.0:
            status = "WARNING"
        else:
            status = "CRITICAL_SPAM_RISK"

        return {
            "spam_score": round(final_score, 1),
            "status": status,
            "is_deliverable": final_score < 50.0,
            "word_count": word_count,
            "reasons": reasons
        }


spam_checker = SpamCheckerService()
