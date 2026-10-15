"""
LangChain Brand Voice & ICP Extraction Pipeline
------------------------------------------------
Leverages LangChain LCEL (LangChain Expression Language) to analyze scraped prospect website
data and extract structured brand tone, positioning, and high-conversion personalization hooks.

INTERVIEW TALKING POINT:
- Why LCEL? LangChain Expression Language provides first-class streaming, async batch support,
  and native fallback capabilities.
- Zero-downtime offline fallback: Generates heuristic brand profiles if OpenAI key is not provided.
"""

from typing import Dict, Any
import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI
from app.core.config import settings
from app.core.logger import logger
from app.pipeline.prompts import BRAND_VOICE_SYSTEM_PROMPT, BRAND_VOICE_USER_PROMPT


class BrandVoicePipeline:
    """Analyzes company positioning and extracts brand voice for hyper-personalized outreach."""

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
            self.prompt = ChatPromptTemplate.from_messages([
                ("system", BRAND_VOICE_SYSTEM_PROMPT),
                ("user", BRAND_VOICE_USER_PROMPT)
            ])
            self.parser = JsonOutputParser()
            self.chain = self.prompt | self.llm | self.parser
        else:
            self.chain = None

    def analyze(
        self,
        company_name: str,
        website_url: str,
        scraped_title: str = "",
        scraped_meta_desc: str = "",
        scraped_headings: list = None,
        scraped_content: str = ""
    ) -> Dict[str, Any]:
        """
        Executes brand voice extraction chain on scraped website data.
        Returns a structured dictionary of brand tone, offering, and personalized hook.
        """
        headings_str = ", ".join(scraped_headings or [])

        # Live LangChain LLM execution
        if self.chain:
            try:
                result = self.chain.invoke({
                    "company_name": company_name or "the company",
                    "website_url": website_url or "",
                    "scraped_title": scraped_title or "",
                    "scraped_meta_desc": scraped_meta_desc or "",
                    "scraped_headings": headings_str or "N/A",
                    "scraped_content": (scraped_content or "")[:1000]
                })
                logger.info(f"LangChain brand voice analysis completed for {company_name}")
                return result
            except Exception as e:
                logger.warning(f"LangChain brand voice execution failed for {company_name}: {e}. Using heuristic.")

        # Heuristic / Offline Fallback Engine
        # Allows full testing without live OpenAI credits
        offering = scraped_title or scraped_meta_desc or f"Services by {company_name}"
        if len(offering) > 80:
            offering = offering[:80] + "..."

        return {
            "brand_tone": "Modern & Growth-Oriented",
            "primary_offering": offering,
            "target_audience": "B2B Decision Makers & Founders",
            "key_pain_points": [
                "Scaling outbound pipeline without headcount explosion",
                "Maintaining high personalization at high volume"
            ],
            "personalized_hook": f"noticed {company_name}'s recent emphasis on {offering}"
        }


brand_voice_pipeline = BrandVoicePipeline()
