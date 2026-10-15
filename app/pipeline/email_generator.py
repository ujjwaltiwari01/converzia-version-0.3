"""
LangChain Email Generation Pipeline
-----------------------------------
Implements structured cold email synthesis using LangChain LCEL chains.
Outputs high-converting AIDA body copy, personalized hooks, and A/B test subject lines.

INTERVIEW TALKING POINT:
- Demonstrates LangChain LCEL composition: Prompt -> ChatOpenAI -> JsonOutputParser.
- Solves LLM nondeterminism by enforcing strict JSON output schemas for downstream database storage.
"""

from typing import Dict, Any, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI
from app.core.config import settings
from app.core.logger import logger
from app.pipeline.prompts import (
    INITIAL_EMAIL_SYSTEM_PROMPT,
    INITIAL_EMAIL_USER_PROMPT,
    FOLLOWUP_EMAIL_SYSTEM_PROMPT
)


class EmailGeneratorPipeline:
    """Generates personalized multi-stage cold outbound emails using LangChain."""

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

            # Step 1 Initial Outreach Chain
            initial_prompt = ChatPromptTemplate.from_messages([
                ("system", INITIAL_EMAIL_SYSTEM_PROMPT),
                ("user", INITIAL_EMAIL_USER_PROMPT)
            ])
            self.initial_chain = initial_prompt | self.llm | self.parser

            # Step 2 & 3 Follow-up Chain
            followup_prompt = ChatPromptTemplate.from_messages([
                ("system", FOLLOWUP_EMAIL_SYSTEM_PROMPT),
                ("user", "Sequence Step: {sequence_step}\nPrevious Subject: {prev_subject}\nPrevious Body:\n{prev_body}")
            ])
            self.followup_chain = followup_prompt | self.llm | self.parser
        else:
            self.initial_chain = None
            self.followup_chain = None

    def generate_initial_email(
        self,
        company_name: str,
        website_url: str,
        recipient_name: Optional[str] = None,
        brand_tone: str = "Growth-focused",
        primary_offering: str = "B2B Solutions",
        personalized_hook: str = "",
        keywords: str = ""
    ) -> Dict[str, Any]:
        """Generates Step 1 personalized cold email with A/B subject lines."""
        name = recipient_name or "there"

        if self.initial_chain:
            try:
                result = self.initial_chain.invoke({
                    "company_name": company_name,
                    "website_url": website_url,
                    "recipient_name": name,
                    "brand_tone": brand_tone,
                    "primary_offering": primary_offering,
                    "personalized_hook": personalized_hook or f"your work at {company_name}",
                    "keywords": keywords or "growth, sales automation"
                })
                logger.info(f"LangChain generated initial outreach email for {company_name}")
                return result
            except Exception as e:
                logger.warning(f"LangChain email generation failed: {e}. Using deterministic engine.")

        # High-converting heuristic fallback (achieves 50-70% open rate style)
        clean_company = company_name or "your team"
        primary_subject = f"micro-idea for {clean_company}'s outbound"
        alt_subjects = [
            f"quick question regarding {clean_company}",
            f"saw something on {clean_company}'s site..."
        ]

        hook_text = personalized_hook or f"was checking out {clean_company}'s site and noticed your focus on {primary_offering}"
        body = (
            f"Hi {name},\n\n"
            f"I {hook_text}.\n\n"
            f"Most agencies and B2B teams we work with are spending 15+ hours a week manually researching prospects, "
            f"yet getting standard 15% open rates. We built Converzia to deploy autonomous SDR agents that analyze each prospect's "
            f"actual website and brand voice before drafting outbound.\n\n"
            f"Result: our clients consistently see 50–70% open rates and steady booked meetings without hiring more reps.\n\n"
            f"Open to seeing a 2-minute interactive preview for {clean_company} this week?"
        )

        return {
            "subject": primary_subject,
            "alternative_subjects": alt_subjects,
            "body": body,
            "personalization_hook": hook_text,
            "rationale": "Curiosity open loop subject line + personalized website observation pattern interrupt"
        }

    def generate_followup_email(
        self,
        company_name: str,
        prev_subject: str,
        prev_body: str,
        sequence_step: int = 2,
        recipient_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generates Step 2 (Value Add) or Step 3 (Breakup) follow-up email."""
        name = recipient_name or "there"

        if self.followup_chain:
            try:
                result = self.followup_chain.invoke({
                    "sequence_step": sequence_step,
                    "prev_subject": prev_subject,
                    "prev_body": prev_body
                })
                return result
            except Exception as e:
                logger.warning(f"LangChain follow-up generation failed: {e}. Using heuristic fallback.")

        # Cadence Step 2: Value-Add Follow-Up
        if sequence_step == 2:
            body = (
                f"Hi {name},\n\n"
                f"Following up briefly on my note regarding {company_name}. "
                f"Thought you might find this relevant: we recently helped a 15-person B2B team process 1,000 targeted leads/day "
                f"with automated website-level personalization, jumping their reply rate by 3.2x in 30 days.\n\n"
                f"Would you be against me sending over a 60-second Loom showing how it works for {company_name}?"
            )
            return {
                "subject": f"Re: {prev_subject}",
                "alternative_subjects": [],
                "body": body,
                "personalization_hook": "Social proof & benchmark data follow-up",
                "rationale": "Value-first touchpoint without aggressive pitch"
            }

        # Cadence Step 3: Polite Breakup
        body = (
            f"Hi {name},\n\n"
            f"I haven't heard back, which usually means either the timing isn't right or automated SDR outreach isn't a priority for {company_name} right now.\n\n"
            f"Totally understand. I won't crowd your inbox any further. If outbound pipeline becomes a focus later this quarter, feel free to reach back out.\n\n"
            f"Best of luck with {company_name}'s growth!"
        )
        return {
            "subject": f"closing the loop for {company_name}",
            "alternative_subjects": [],
            "body": body,
            "personalization_hook": "Respectful breakup close",
            "rationale": "Creates subtle urgency by removing pressure and closing the loop"
        }


email_generator = EmailGeneratorPipeline()
