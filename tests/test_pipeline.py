"""
Unit Tests for Brand Voice & Email Generation Pipeline
"""
import pytest
from app.pipeline.brand_voice import brand_voice_pipeline
from app.pipeline.email_generator import email_generator
from app.pipeline.spam_checker import spam_checker

def test_brand_voice_analysis():
    profile = brand_voice_pipeline.analyze(
        company_name="SmartSites",
        website_url="https://smartsites.com",
        scraped_title="SmartSites - Top Rated Digital Marketing Agency",
        scraped_meta_desc="Full service digital agency specializing in SEO, PPC and Web Design"
    )
    assert "brand_tone" in profile
    assert "primary_offering" in profile
    assert "personalized_hook" in profile

def test_email_generator_initial():
    email = email_generator.generate_initial_email(
        company_name="SmartSites",
        website_url="https://smartsites.com",
        recipient_name="Mike",
        personalized_hook="noticed your focus on full service digital marketing"
    )
    assert "subject" in email
    assert "body" in email
    assert "SmartSites" in email["subject"] or "SmartSites" in email["body"]
    assert "Mike" in email["body"]

def test_spam_checker_clean_email():
    res = spam_checker.analyze(
        subject="micro-idea for SmartSites",
        body="Hi Mike,\n\nSaw your team's work on digital marketing. Are you open to seeing a 2-min preview?\n\nBest,\nConverzia"
    )
    assert res["is_deliverable"] is True
    assert res["spam_score"] < 25.0

def test_spam_checker_flags_spam_triggers():
    res = spam_checker.analyze(
        subject="ACT NOW! 100% FREE GUARANTEED CASH BONUS!!!",
        body="Earn $$$ fast with no catch! Click here now to get free gift and make money right away!"
    )
    assert res["spam_score"] > 50.0
    assert len(res["reasons"]) > 0
