"""
Unit Tests for Autonomous SDR Agent
"""
import pytest
from app.agents.sdr_agent import sdr_agent

def test_sdr_agent_meeting_request():
    reply = "Sounds great, can you share a calendar link to book a time?"
    decision = sdr_agent.evaluate_reply(reply, company_name="Acme Corp")
    assert decision["classification"] == "MEETING_REQUESTED"
    assert decision["recommended_action"] == "SEND_CALENDAR_LINK"
    assert decision["suggested_reply"] is not None

def test_sdr_agent_pricing_objection():
    reply = "We are interested but budget is very tight right now. How much is it?"
    decision = sdr_agent.evaluate_reply(reply, company_name="Acme Corp")
    assert decision["classification"] == "OBJECTION_PRICING"
    assert decision["recommended_action"] == "DRAFT_OBJECTION_HANDLING"

def test_sdr_agent_unsubscribe():
    reply = "Please unsubscribe me immediately and stop sending emails."
    decision = sdr_agent.evaluate_reply(reply, company_name="Acme Corp")
    assert decision["classification"] == "UNSUBSCRIBE"
    assert decision["recommended_action"] == "OPT_OUT"
