"""
Autonomous SDR Agent Engine
---------------------------
Analyzes prospect replies, classifies buyer intent, handles objections,
and executes autonomous sales decisions.

SYSTEM DESIGN / AUTONOMOUS SDR ARCHITECTURE:
- Traditional outbound tools blindly blast 3 emails on a timer, often sending follow-ups
  even after a prospect replied "Not interested" or "Let's meet tomorrow".
- Converzia's SDR Agent is event-driven:
  1. Ingests inbound reply webhook.
  2. Classifies intent via LangChain agent reasoning (Meeting, Interested, Objection, OOF, Opt-Out).
  3. Executes autonomous action:
     - Meeting Requested -> Immediately halts sequence, sends calendar booking link, syncs CRM.
     - Objection -> Synthesizes empathetic objection handler grounded in prospect's brand voice.
     - Out of Office -> Extracts return date, pauses cadence until prospect is back at work.
     - Opt-out -> Permanently flags lead as OPT_OUT to protect domain reputation.
"""

from typing import Dict, Any, Optional
import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI
from app.core.config import settings
from app.core.logger import logger
from app.pipeline.prompts import SDR_AGENT_SYSTEM_PROMPT


class SDRAgent:
    """Autonomous SDR decision engine for reply analysis and objection handling."""

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model_name = settings.OPENAI_MODEL
        self.temperature = settings.LLM_TEMPERATURE

        if self.api_key:
            self.llm = ChatOpenAI(
                model=self.model_name,
                temperature=self.temperature,
                openai_api_key=self.api_key
            )
            self.parser = JsonOutputParser()
            self.prompt = ChatPromptTemplate.from_messages([
                ("system", SDR_AGENT_SYSTEM_PROMPT),
                ("user", "Prospect Reply Text:\n\"\"\"{reply_text}\"\"\"\n\nLead Company: {company_name}")
            ])
            self.chain = self.prompt | self.llm | self.parser
        else:
            self.chain = None

    def evaluate_reply(
        self,
        reply_text: str,
        company_name: str = "the prospect",
        lead_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Processes an incoming prospect email and outputs structured action decision.
        """
        # Execute LangChain LCEL agent chain if OpenAI credentials available
        if self.chain:
            try:
                decision = self.chain.invoke({
                    "reply_text": reply_text,
                    "company_name": company_name
                })
                logger.info(
                    f"SDR Agent classified reply for {company_name}: "
                    f"{decision.get('classification')} -> Action: {decision.get('recommended_action')}"
                )
                return decision
            except Exception as e:
                logger.warning(f"SDR Agent chain failed: {e}. Executing heuristic classifier.")

        # High-Fidelity Heuristic Intent Classifier (Runs 100% offline for evaluations)
        cleaned = reply_text.lower().strip()

        # 1. Unsubscribe / Opt-Out
        if any(w in cleaned for w in ["unsubscribe", "remove me", "stop emailing", "take me off", "not interested"]):
            return {
                "classification": "UNSUBSCRIBE",
                "confidence_score": 0.98,
                "reasoning": "Prospect requested removal from outreach. Immediate compliance required.",
                "recommended_action": "OPT_OUT",
                "suggested_reply": None,
                "delay_hours": 0
            }

        # 2. Meeting Requested
        if any(w in cleaned for w in ["calendar", "schedule", "call", "zoom", "meet", "book a time", "let's chat", "tuesday", "thursday", "tomorrow"]):
            return {
                "classification": "MEETING_REQUESTED",
                "confidence_score": 0.95,
                "reasoning": "Prospect expressed direct buying intent and requested a meeting.",
                "recommended_action": "SEND_CALENDAR_LINK",
                "suggested_reply": (
                    f"Great to connect! You can pick a 15-minute slot that works best for your schedule here: "
                    f"https://cal.com/converzia-demo\n\nLooking forward to speaking!"
                ),
                "delay_hours": 0
            }

        # 3. Out of Office
        if any(w in cleaned for w in ["out of the office", "on leave", "vacation", "returning on", "away from my desk"]):
            return {
                "classification": "OUT_OF_OFFICE",
                "confidence_score": 0.92,
                "reasoning": "Automated out-of-office autoreply detected. Pausing cadence.",
                "recommended_action": "PAUSE_CADENCE",
                "suggested_reply": None,
                "delay_hours": 72
            }

        # 4. Pricing / Budget Objection
        if any(w in cleaned for w in ["cost", "price", "budget", "expensive", "how much"]):
            return {
                "classification": "OBJECTION_PRICING",
                "confidence_score": 0.88,
                "reasoning": "Prospect concerned about cost before seeing the product ROI.",
                "recommended_action": "DRAFT_OBJECTION_HANDLING",
                "suggested_reply": (
                    f"Totally fair question on pricing. Our model is purely performance-aligned—most teams find "
                    f"Converzia replaces about $4,000/mo in manual SDR tool subscriptions while doubling booked meetings.\n\n"
                    f"Happy to walk through the exact numbers for {company_name} if you have 5 minutes this week?"
                ),
                "delay_hours": 2
            }

        # 5. General Interest
        return {
            "classification": "INTERESTED",
            "confidence_score": 0.85,
            "reasoning": "Prospect is curious and receptive to learning more.",
            "recommended_action": "DRAFT_OBJECTION_HANDLING",
            "suggested_reply": (
                f"Glad to hear this resonated! In short: Converzia autonomously visits prospect websites, "
                f"understands their brand voice, and runs personalized multi-touch sequences.\n\n"
                f"Would you be open to a 2-minute Loom showing how this applies to {company_name}?"
            ),
            "delay_hours": 1
        }


sdr_agent = SDRAgent()
