# Radian Marketing Cold Email Automation
# This script automates the process of generating and sending personalized cold emails

import streamlit as st
import pandas as pd
import time
import openai
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
import email_validator
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# ----------------------------
# 🔑 YOUR API KEYS
# ----------------------------
# For local development, load .env (optional, not needed on Streamlit Cloud)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import streamlit as st
import os

def get_secret(key):
    try:
        return st.secrets[key]
    except Exception:
        return os.getenv(key)

OPENAI_API_KEY = get_secret("OPENAI_API_KEY")
BREVO_API_KEY = get_secret("BREVO_API_KEY")
SENDER_NAME = get_secret("SENDER_NAME")
SENDER_EMAIL = get_secret("SENDER_EMAIL")
HUBSPOT_TOKEN = get_secret("HUBSPOT_TOKEN")

openai.api_key = OPENAI_API_KEY

config = sib_api_v3_sdk.Configuration()
config.api_key['api-key'] = BREVO_API_KEY
email_api = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(config))



# ----------------------------
# 📬 Email Validation
# ----------------------------
def is_valid_email_address(email):
    try:
        if isinstance(email, bytes):
            email = email.decode("utf-8")
        email_validator.validate_email(email)
        return True
    except email_validator.EmailNotValidError:
        return False

def is_role_based_email(email):
    role_keywords = ["info", "support", "admin", "contact", "sales", "team", "hello"]
    local_part = email.split("@")[0].lower()
    return any(local_part.startswith(role) for role in role_keywords)

# ----------------------------
# 🌐 Website Scraping for Personalization
# ----------------------------
def scrape_website_info(website_url):
    """Scrape website title and meta description for personalization."""
    try:
        resp = requests.get(website_url, timeout=8)
        soup = BeautifulSoup(resp.text, "html.parser")
        title = soup.title.string.strip() if soup.title else ""
        meta_desc = ""
        desc_tag = soup.find("meta", attrs={"name": "description"})
        if desc_tag and desc_tag.get("content"):
            meta_desc = desc_tag["content"].strip()
        return title, meta_desc
    except Exception as e:
        return "", ""

# ----------------------------
# ✍️ Email Generation
# ----------------------------
def generate_email(company, website, keywords, recipient_name=None):
    # Now this works!
    title, meta_desc = scrape_website_info(website)
    website_info = f"Website Title: {title}\nMeta Description: {meta_desc}" if (title or meta_desc) else "No website info found."
    # Improved subject line prompt using awareness-stage examples for inspiration
    prompt = f"""
You are the world's most ingenious, psychologically-savvy, and results-obsessed B2B cold email copywriter and prompt engineer. Your mission: craft the single most curiosity-inducing, human, and irresistible cold email ever written for Converzia—an AI-powered sales assistant that acts as a company’s best sales rep at scale.

========================
ULTIMATE GOAL
========================
Achieve a 100% open rate and a 100%+ reply rate. Your email must be so compelling, so personally relevant, and so emotionally resonant that B2B agency decision-makers in the USA (marketing, digital, creative, SaaS, tech, etc.) feel an overwhelming urge to open, read, and reply—immediately. They get hundreds of cold emails—yours must be the ONLY one they remember, forward, and respond to.

========================
ABOUT CONVERZIA
========================
- Converzia is an AI-powered sales assistant that visits a prospect’s website, understands their business, tone, and audience, and crafts a cold email that feels like a warm, thoughtful introduction.
- It identifies missed opportunities, aligns those gaps with Converzia’s AI-powered outreach, and tracks opens, replies, bounces, schedules follow-ups, and integrates with CRM.
- The goal is to make every prospect feel seen, understood, and genuinely helped—not pitched.

========================
YOUR TASK
========================
- Write a cold email for Converzia targeting B2B agency decision-makers in the USA (marketing, digital, creative, SaaS, tech, etc.).
- The subject line **must include the company name** and be so curiosity-driven, so hyper-personalized, and so psychologically irresistible that it achieves a 100% open rate—think like a world-class copy chief, using advanced psychological triggers, open loops, pattern interrupts, and deep personalization.
- The email body must be ultra-human, deeply empathetic, and feel like a real conversation from a peer who truly understands their business and cares about their success.
- Use the AIDA method (Attention, Interest, Desire, Action) for the body.
- The email must be quick to read (max 8 sentences), written in natural, everyday English, and deeply personal—like you genuinely care.
- The CTA must be so soft, so easy, and so inviting that the recipient feels it would be a pleasure to book a quick chat or meeting.

========================
SUBJECT LINE STRATEGY
========================
- Make the subject line more specific to the recipient’s website, service, or recent activity.
- Avoid repeating subject lines like “Noticed something on your site…” — it becomes predictable.
- Use open loops to trigger curiosity (e.g., “Enrollment strategy tip you might’ve missed”).
- Add industry-specific language (e.g., "client journey gaps on your homepage").
- Experiment with micro-story teasers (e.g., “A quick story about a school that doubled signups”).
- The subject line must create an irresistible open loop, spark intense curiosity, and reference something unique about their business, website, or a recent achievement, challenge, or trend.
- **The subject line must include the company name ({company}) in a natural, non-spammy way.**
- Use advanced psychological triggers: open loops, pattern interrupts, micro-personalization, FOMO, social proof, and subtle urgency—but never hype or manipulation.
- Examples for inspiration (do NOT copy, but adapt the style and intent):
    - "Saw something on {company}’s site—can I share a wild idea?"
    - "Your agency’s secret edge? (1-min thought inside)"
    - "Noticed {{unique detail}} at {company}—is anyone else missing this?"
    - "Quick question about {company}—bet you haven’t heard this before"
    - "If I were you at {company}, I’d want to know this"
    - "A micro-idea for {company}—promise it’s not a pitch"
    - "What most agencies miss (but {company} could nail)"
    - "How {company} could double replies this month (no sales pitch)"
    - "If you only open one email today at {company}, make it this one"
- Avoid all generic, salesy, or spammy language. Make it feel like a personal note from a peer, not a vendor.
- The subject line must be so good that the recipient feels compelled to open immediately, even if they never open cold emails.

========================
EMAIL BODY STRATEGY (AIDA)
========================
- **Attention (First Line):**
    - Give a very specific compliment — not just “great work,” but “your lead-gen form design is a masterclass in simplicity.”
    - Reference a specific project, page, or client they showcased.
    - Show you actually explored their site — e.g., “I saw you helped XYZ Academy boost enrollments by 32%.”
    - Reference a testimonial, a client name, their location, or their website tone (“Your conversational tone made me smile — rare in edtech!”).
    - If scraping sites, use homepage header, taglines, latest blog headlines, testimonials, recent client results.
    - Use those elements in the first 2 sentences to make the email feel unique.

- **Interest (Pain/Challenge):**
    - Identify industry-specific pain points, not general ones.
    - For schools: “Nurturing leads from interest to enrollment is tricky.”
    - For video agencies: “Scaling creative without losing the human spark is tough.”
    - Avoid vague lines like “I know personalization at scale is hard” — make it their problem.
    - Use micro-insights: “You’re doing amazing work, but your case study headlines don’t sell the value you delivered.”
    - If possible, reference a recent trend, news, or shift in their industry that’s relevant to their business.

- **Desire (How Converzia Helps):**
    - Don’t repeat the same value prop across emails — tailor it by niche.
    - Use metaphors or analogies for clarity and memorability:
        - “Converzia is like your creative director turned into an AI sales rep.”
        - “It’s like cloning your best rep and setting them loose on autopilot.”
    - Add mini case-study-style examples: “One agency used us and saw a 3.2x reply rate in 2 weeks.”
    - Emphasize the feeling (relief, clarity, connection) — not just the function.
    - Never say “AI agent” in a robotic way — frame it as an assistant, partner, or virtual team member.
    - Avoid filler like “seamlessly integrates with your CRM” — show why that matters.

- **Action (Call-To-Action):**
    - Make it feel like a tailored offer, not a standard pitch.
    - Instead of “Would you be open to a quick chat?” try:
        → “Can I show you what this might look like for [their company name]?”
    - Use curiosity + ease:
        “Want to see what this would write for your next prospect?”
    - End warm and human:
        “No pressure, just thought it might be fun to explore.”
    - Add rejection-safe endings: “If you’re not the right person, feel free to point me in the right direction.”

========================
FORMAT & DELIVERY TIPS
========================
- Do NOT include any line like "If this isn't for you, just reply STOP." or similar opt-out language.
- Keep sentences short and snappy — no more than 2 lines per paragraph.
- Use max 6–8 sentences in total.
- Use white space generously to make the email scannable.
- Never say “AI agent” in a robotic way — frame it as an assistant, partner, or virtual team member.
- Avoid filler like “seamlessly integrates with your CRM” — show why that matters.
- Use formatting (line breaks, short paragraphs) to make the email easy to scan and inviting to read.
- If you use a question, make it open-ended and thought-provoking, not yes/no.
- The sign-off should feel warm and genuine, not formulaic. Always sign off as "Bhaskar".
- If you mention Converzia, do so in a way that feels natural and relevant to their needs.
- Avoid all buzzwords, jargon, or technical language.
- Make the email feel like it was written by someone who truly cares about their success.
- If you can, reference a shared value, goal, or challenge.
- The email should feel like the start of a partnership, not a transaction.
- If you use a statistic or fact, make sure it’s relevant and adds value.
- The subject line and first sentence should work together to create curiosity and relevance.
- The email should be so good that the recipient wants to forward it to a colleague.
- If you can, include a “micro-offer” (e.g., a quick tip, resource, or idea) that adds value even if they don’t reply.
- The email should feel like a breath of fresh air compared to the usual cold outreach.
- If you reference a competitor, do so respectfully and only if it adds value.
- The email should be timeless—relevant today and in the future.
- If you use a metaphor or analogy, make it vivid and memorable.
- The email should feel like a conversation starter, not a monologue.
- If you can, reference a recent achievement, milestone, or news about their company.
- The email should be so personalized that it couldn’t be sent to anyone else.
- If you use humor, make sure it’s subtle and appropriate.
- The email should feel like a handwritten note, not a mass email.
- If you reference a pain point, make it specific and empathetic.
- The email should be so good that the recipient wants to reply, even if just to say thank you.
- If you use a call-to-action, make it easy to say yes to.
- The email should feel like a favor, not a request.
- If you can, reference a mutual connection, interest, or value.
- The email should be so well-written that it stands out in their inbox.
- If you use a compliment, make it specific and genuine.
- The email should feel like the beginning of a valuable relationship.
- If you reference a challenge, make it one that only someone who understands their business would know.
- The email should be so relevant that the recipient feels compelled to respond.
- If you use a story, make it short, relevant, and memorable.
- The email should feel like it was written just for them, at this moment, for this reason.
- If you use a statistic, make it surprising and relevant.
- The email should be so good that the recipient wants to keep it for future reference.
- If you use a question, make it one that sparks curiosity and conversation.
- The email should feel like a conversation between equals.
- If you reference a goal, make it one that’s important to them.
- The email should be so helpful that the recipient feels grateful.
- If you use a resource, make it relevant and valuable.
- The email should feel like a gift, not a pitch.
- If you reference a trend, make it one that’s relevant to their business.
- The email should be so good that the recipient wants to share it with their team.
- If you use a CTA, make it feel like an invitation, not an obligation.
- The email should feel like the start of a partnership, not a transaction.
- If you can, add a “micro-offer” or insight that makes the email valuable even if they never reply.
- The email must be so good, so specific, and so relevant that the recipient feels it was written just for them, at this moment, for this reason—and they feel compelled to open, read, and reply.

========================
COPY VARIETY & ORIGINALITY
========================
- Don’t copy-paste the same structure — vary the:
    - Length
    - Sentence rhythm
    - Type of insight
- Inject humor or playful analogies when appropriate.
    - E.g., “It’s like giving your cold outreach a triple-shot espresso and a personal stylist.”
- Show that you’ve done homework unique to each recipient — use real names if available, or client references.

========================
PERSONALIZATION DEPTH
========================
- Reference:
    - A testimonial on their site
    - A specific client name
    - Their location (e.g., “Loved how you serve California charter schools”)
    - Their website tone (“Your conversational tone made me smile — rare in edtech!”)
- If you're scraping sites, scrape:
    - Homepage header
    - Taglines
    - Latest blog headlines
    - Testimonials
    - Recent client results
- Use those elements in the first 2 sentences to make the email feel unique.

========================
TRAINING YOUR LLM
========================
- Train on multi-niche examples (SaaS, agencies, edtech, production houses).
- Feed in 20–50 high-performing real cold emails as prompts with labeled AIDA structure.
- Add rejection-safe endings: “If you’re not the right person, feel free to point me in the right direction.”
- Use prompt tags in your LLM like {{industry}}, {{recent_news}}, {{unique_offer}}, {{pain_point}}.
- Generate multiple email styles (e.g., friendly peer tone, expert consultant tone, quirky disruptor tone).

========================
FORMATTING & RULES
========================
- Output ONLY the subject line and email body (no extra commentary).
- The subject line must include the company name ({company}) in a natural, non-spammy way.
- The email body must be a natural, conversational, well-formatted email with short, punchy paragraphs (1–2 sentences each), max 8 sentences total.
- Do NOT include any lines like "- 1st:", "- 2nd:", etc. in the body—write it as a real email, not a template or outline.
- Do NOT use any emojis anywhere.
- Write in natural, everyday English—like a real person, not a robot.
- No ALL CAPS, hype, or filler.
- No overexplaining—be lean, warm, and strategic.
- The reader should feel seen, understood, and genuinely helped—not pitched.
- Always sign off as "Bhaskar" (never use [Your Name] or any other placeholder).

========================
INPUTS
========================
Company: {company}
Website: {website}
Keywords: {keywords}
Website Info (scraped): {website_info}

========================
EMAIL FORMAT
========================
Subject: <short, ultra-personalized, curiosity-driven subject that includes the company name>
Body:

<the full, properly formatted email body as described above, with no outline or bullet points, and no emojis, and signed off as Bhaskar>
"""

    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=700,
    )
    result = response.choices[0].message.content.strip()

    # Extract subject and body, ensuring subject is not duplicated in the body
    subject = ""
    body = ""
    lines = result.splitlines()
    found_subject = False
    found_body = False
    body_lines = []

    for line in lines:
        if not found_subject and line.lower().startswith("subject:"):
            subject = line.split(":", 1)[1].strip()
            found_subject = True
        elif line.lower().startswith("body:"):
            found_body = True
            continue  # skip the "Body:" line itself
        elif found_body:
            body_lines.append(line)

    # If subject/body not found, fallback to defaults
    if not subject:
        subject = "AI Outreach That Converts"
    if not body_lines:
        # fallback: use everything except subject line
        body_lines = [l for l in lines if not l.lower().startswith("subject:") and not l.lower().startswith("body:")]

    body = "\n".join(body_lines).strip()

    # Remove subject line if it accidentally appears at the top of the body
    if body.lower().startswith(subject.lower()):
        body = body[len(subject):].lstrip(" :\n")

    # --- Remove LLM-generated greeting at the top ---
    import re
    body = re.sub(r"^(hey|hi|hello)[^\n]*,?\s*\n+", "", body, flags=re.IGNORECASE)

    # --- Remove emojis from the body ---
    body = re.sub(r"[^\w\s,.!?@%&:;\"'()\[\]\-\/\n]", "", body)

    # --- Remove numbered/bullet formatting at the start of lines ---
    body = re.sub(r"^\s*[\-\*\d]+\s*[:.\)]\s*", "", body, flags=re.MULTILINE)

    # --- Split into short paragraphs (1–2 sentences per paragraph) ---
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    paragraphs = []
    current = ""
    for line in lines:
        if current:
            current += " " + line
        else:
            current = line
        # If the line ends with a period/question mark/exclamation, treat as paragraph end
        if current and current[-1] in ".!?":
            paragraphs.append(current.strip())
            current = ""
    if current:
        paragraphs.append(current.strip())
    body = "\n\n".join(paragraphs)

    # --- Add greeting at the top ---
    if recipient_name and recipient_name.strip().lower() not in ["", "none"]:
        greeting = f"Hey {recipient_name.strip()},"
    elif company and company.strip():
        greeting = f"Hey {company.strip()},"
    elif website and website.strip():
        domain = re.sub(r"https?://(www\.)?", "", website.strip(), flags=re.IGNORECASE)
        domain = domain.split("/")[0]
        greeting = f"Hey {domain},"
    else:
        greeting = "Hey there,"

    body = f"{greeting}\n\n{body}"

    if "stop" not in body.lower():
        body += "\n\nIf this isn't for you, just reply STOP."

    return subject, body

def generate_followup_email(company, website, keywords, prev_subject, prev_body, recipient_name=None):
    # Scrape website info for personalization
    title, meta_desc = scrape_website_info(website)
    website_info = f"Website Title: {title}\nMeta Description: {meta_desc}" if (title or meta_desc) else "No website info found."

    prompt = f"""
You are the world's most ingenious, psychologically-savvy, and results-obsessed B2B cold email copywriter and prompt engineer. Your mission: craft the single most curiosity-inducing, human, and irresistible follow-up cold email ever written for Converzia—an AI-powered sales assistant that acts as a company’s best sales rep at scale.

========================
ULTIMATE GOAL
========================
Achieve a 100% open rate and a 100%+ reply rate with this follow-up. Your email must be so compelling, so personally relevant, and so emotionally resonant that B2B agency decision-makers in the USA (marketing, digital, creative, SaaS, tech, etc.) feel an overwhelming urge to open, read, and reply—immediately. They get hundreds of cold emails—yours must be the ONLY one they remember, forward, and respond to.

========================
ABOUT CONVERZIA
========================
- Converzia is an AI-powered sales assistant that visits a prospect’s website, understands their business, tone, and audience, and crafts a cold email that feels like a warm, thoughtful introduction.
- It identifies missed opportunities, aligns those gaps with Converzia’s AI-powered outreach, and tracks opens, replies, bounces, schedules follow-ups, and integrates with CRM.
- The goal is to make every prospect feel seen, understood, and genuinely helped—not pitched.

========================
YOUR TASK
========================
- Write a follow-up cold email for Converzia targeting B2B agency decision-makers in the USA (marketing, digital, creative, SaaS, tech, etc.).
- Reference the previous outreach (subject: "{prev_subject}"), show genuine interest, and offer a new value or insight based on their website or business.
- The subject line must be so curiosity-driven, so hyper-personalized, and so psychologically irresistible that it achieves a 100% open rate—think like a world-class copy chief, using advanced psychological triggers, open loops, pattern interrupts, FOMO, and deep personalization.
- The subject line must include the company name ({company}) in a natural, non-spammy way.
- The email body must be ultra-human, deeply empathetic, and feel like a real conversation from a peer who truly understands their business and cares about their success.
- Use the AIDA method (Attention, Interest, Desire, Action) for the body.
- The email must be quick to read (max 8 sentences), written in natural, everyday English, and deeply personal—like you genuinely care.
- The CTA must be so soft, so easy, and so inviting that the recipient feels it would be a pleasure to book a quick chat or meeting.

========================
SUBJECT LINE STRATEGY
========================
- Make the subject line more specific to the recipient’s website, service, or recent activity.
- Avoid repeating subject lines like “Noticed something on your site…” — it becomes predictable.
- Use open loops to trigger curiosity (e.g., “Enrollment strategy tip you might’ve missed”).
- Add industry-specific language (e.g., "client journey gaps on your homepage").
- Experiment with micro-story teasers (e.g., “A quick story about a school that doubled signups”).
- The subject line must create an irresistible open loop, spark intense curiosity, and reference something unique about their business, website, or a recent achievement, challenge, or trend.
- **The subject line must include the company name ({company}) in a natural, non-spammy way.**
- Use advanced psychological triggers: open loops, pattern interrupts, micro-personalization, FOMO, social proof, and subtle urgency—but never hype or manipulation.
- Examples for inspiration (do NOT copy, but adapt the style and intent):
    - "Saw something on {company}’s site—can I share a wild idea?"
    - "Your agency’s secret edge? (1-min thought inside)"
    - "Noticed {{unique detail}} at {company}—is anyone else missing this?"
    - "Quick question about {company}—bet you haven’t heard this before"
    - "If I were you at {company}, I’d want to know this"
    - "A micro-idea for {company}—promise it’s not a pitch"
    - "What most agencies miss (but {company} could nail)"
    - "How {company} could double replies this month (no sales pitch)"
    - "If you only open one email today at {company}, make it this one"
- Avoid all generic, salesy, or spammy language. Make it feel like a personal note from a peer, not a vendor.
- The subject line must be so good that the recipient feels compelled to open immediately, even if they never open cold emails.

========================
EMAIL BODY STRATEGY (AIDA)
========================
- **Attention (First Line):**
    - Reference the previous email (subject: "{prev_subject}") in a way that feels natural and personal.
    - Give a very specific compliment — not just “great work,” but “your lead-gen form design is a masterclass in simplicity.”
    - Reference a specific project, page, or client they showcased.
    - Show you actually explored their site — e.g., “I saw you helped XYZ Academy boost enrollments by 32%.”
    - Reference a testimonial, a client name, their location, or their website tone (“Your conversational tone made me smile — rare in edtech!”).
    - If scraping sites, use homepage header, taglines, latest blog headlines, testimonials, recent client results.
    - Use those elements in the first 2 sentences to make the email feel unique.

- **Interest (Pain/Challenge):**
    - Identify industry-specific pain points, not general ones.
    - For schools: “Nurturing leads from interest to enrollment is tricky.”
    - For video agencies: “Scaling creative without losing the human spark is tough.”
    - Avoid vague lines like “I know personalization at scale is hard” — make it their problem.
    - Use micro-insights: “You’re doing amazing work, but your case study headlines don’t sell the value you delivered.”
    - If possible, reference a recent trend, news, or shift in their industry that’s relevant to their business.

- **Desire (How Converzia Helps):**
    - Don’t repeat the same value prop across emails — tailor it by niche.
    - Use metaphors or analogies for clarity and memorability:
        - “Converzia is like your creative director turned into an AI sales rep.”
        - “It’s like cloning your best rep and setting them loose on autopilot.”
    - Add mini case-study-style examples: “One agency used us and saw a 3.2x reply rate in 2 weeks.”
    - Emphasize the feeling (relief, clarity, connection) — not just the function.
    - Never say “AI agent” in a robotic way — frame it as an assistant, partner, or virtual team member.
    - Avoid filler like “seamlessly integrates with your CRM” — show why that matters.

- **Action (Call-To-Action):**
    - Make it feel like a tailored offer, not a standard pitch.
    - Instead of “Would you be open to a quick chat?” try:
        → “Can I show you what this might look like for [their company name]?”
    - Use curiosity + ease:
        “Want to see what this would write for your next prospect?”
    - End warm and human:
        “No pressure, just thought it might be fun to explore.”
    - Add rejection-safe endings: “If you’re not the right person, feel free to point me in the right direction.”

========================
FORMAT & DELIVERY TIPS
========================
- Do NOT include any line like "If this isn't for you, just reply STOP." or similar opt-out language.
- Keep sentences short and snappy — no more than 2 lines per paragraph.
- Use max 6–8 sentences in total.
- Use white space generously to make the email scannable.
- Never say “AI agent” in a robotic way — frame it as an assistant, partner, or virtual team member.
- Avoid filler like “seamlessly integrates with your CRM” — show why that matters.
- Use formatting (line breaks, short paragraphs) to make the email easy to scan and inviting to read.
- If you use a question, make it open-ended and thought-provoking, not yes/no.
- The sign-off should feel warm and genuine, not formulaic. Always sign off as "Bhaskar".
- If you mention Converzia, do so in a way that feels natural and relevant to their needs.
- Avoid all buzzwords, jargon, or technical language.
- Make the email feel like it was written by someone who truly cares about their success.
- If you can, reference a shared value, goal, or challenge.
- The email should feel like the start of a partnership, not a transaction.
- If you use a statistic or fact, make sure it’s relevant and adds value.
- The subject line and first sentence should work together to create curiosity and relevance.
- The email should be so good that the recipient wants to forward it to a colleague.
- If you can, include a “micro-offer” (e.g., a quick tip, resource, or idea) that adds value even if they don’t reply.
- The email should feel like a breath of fresh air compared to the usual cold outreach.
- If you reference a competitor, do so respectfully and only if it adds value.
- The email should be timeless—relevant today and in the future.
- If you use a metaphor or analogy, make it vivid and memorable.
- The email should feel like a conversation starter, not a monologue.
- If you can, reference a recent achievement, milestone, or news about their company.
- The email should be so personalized that it couldn’t be sent to anyone else.
- If you use humor, make sure it’s subtle and appropriate.
- The email should feel like a handwritten note, not a mass email.
- If you reference a pain point, make it specific and empathetic.
- The email should be so good that the recipient wants to reply, even if just to say thank you.
- If you use a call-to-action, make it easy to say yes to.
- The email should feel like a favor, not a request.
- If you can, reference a mutual connection, interest, or value.
- The email should be so well-written that it stands out in their inbox.
- If you use a compliment, make it specific and genuine.
- The email should feel like the beginning of a valuable relationship.
- If you reference a challenge, make it one that only someone who understands their business would know.
- The email should be so relevant that the recipient feels compelled to respond.
- If you use a story, make it short, relevant, and memorable.
- The email should feel like it was written just for them, at this moment, for this reason.
- If you use a statistic, make it surprising and relevant.
- The email should be so good that the recipient wants to keep it for future reference.
- If you use a question, make it one that sparks curiosity and conversation.
- The email should feel like a conversation between equals.
- If you reference a goal, make it one that’s important to them.
- The email should be so helpful that the recipient feels grateful.
- If you use a resource, make it relevant and valuable.
- The email should feel like a gift, not a pitch.
- If you reference a trend, make it one that’s relevant to their business.
- The email should be so good that the recipient wants to share it with their team.
- If you use a CTA, make it feel like an invitation, not an obligation.
- The email should feel like the start of a partnership, not a transaction.
- If you can, add a “micro-offer” or insight that makes the email valuable even if they never reply.
- The email must be so good, so specific, and so relevant that the recipient feels it was written just for them, at this moment, for this reason—and they feel compelled to open, read, and reply.

========================
COPY VARIETY & ORIGINALITY
========================
- Don’t copy-paste the same structure — vary the:
    - Length
    - Sentence rhythm
    - Type of insight
- Inject humor or playful analogies when appropriate.
    - E.g., “It’s like giving your cold outreach a triple-shot espresso and a personal stylist.”
- Show that you’ve done homework unique to each recipient — use real names if available, or client references.

========================
PERSONALIZATION DEPTH
========================
- Reference:
    - A testimonial on their site
    - A specific client name
    - Their location (e.g., “Loved how you serve California charter schools”)
    - Their website tone (“Your conversational tone made me smile — rare in edtech!”)
- If you're scraping sites, scrape:
    - Homepage header
    - Taglines
    - Latest blog headlines
    - Testimonials
    - Recent client results
- Use those elements in the first 2 sentences to make the email feel unique.

========================
TRAINING YOUR LLM
========================
- Train on multi-niche examples (SaaS, agencies, edtech, production houses).
- Feed in 20–50 high-performing real cold emails as prompts with labeled AIDA structure.
- Add rejection-safe endings: “If you’re not the right person, feel free to point me in the right direction.”
- Use prompt tags in your LLM like {{industry}}, {{recent_news}}, {{unique_offer}}, {{pain_point}}.
- Generate multiple email styles (e.g., friendly peer tone, expert consultant tone, quirky disruptor tone).

========================
FORMATTING & RULES
========================
- Output ONLY the subject line and email body (no extra commentary).
- The subject line must include the company name ({company}) in a natural, non-spammy way.
- The email body must be a natural, conversational, well-formatted email with short, punchy paragraphs (1–2 sentences each), max 8 sentences total.
- Do NOT include any lines like "- 1st:", "- 2nd:", etc. in the body—write it as a real email, not a template or outline.
- Do NOT use any emojis anywhere.
- Write in natural, everyday English—like a real person, not a robot.
- No ALL CAPS, hype, or filler.
- No overexplaining—be lean, warm, and strategic.
- The reader should feel seen, understood, and genuinely helped—not pitched.
- Always sign off as "Bhaskar" (never use [Your Name] or any other placeholder).

========================
INPUTS
========================
Company: {company}
Website: {website}
Keywords: {keywords}
Website Info (scraped): {website_info}
Previous Email Subject: {prev_subject}
Previous Email Body: {prev_body}

========================
EMAIL FORMAT
========================
Subject: <short, ultra-personalized, curiosity-driven subject that includes the company name>
Body:

<the full, properly formatted email body as described above, with no outline or bullet points, and no emojis, and signed off as Bhaskar>
"""

    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=900,
    )
    result = response.choices[0].message.content.strip()

    # Extract subject and body, ensuring subject is not duplicated in the body
    subject = ""
    body = ""
    lines = result.splitlines()
    found_subject = False
    found_body = False
    body_lines = []

    for line in lines:
        if not found_subject and line.lower().startswith("subject:"):
            subject = line.split(":", 1)[1].strip()
            found_subject = True
        elif line.lower().startswith("body:"):
            found_body = True
            continue  # skip the "Body:" line itself
        elif found_body:
            body_lines.append(line)

    # If subject/body not found, fallback to defaults
    if not subject:
        subject = f"Quick Follow-up: {company}"
    if not body_lines:
        # fallback: use everything except subject line
        body_lines = [l for l in lines if not l.lower().startswith("subject:") and not l.lower().startswith("body:")]

    body = "\n".join(body_lines).strip()

    # Remove subject line if it accidentally appears at the top of the body
    if body.lower().startswith(subject.lower()):
        body = body[len(subject):].lstrip(" :\n")

    # --- Remove LLM-generated greeting at the top ---
    import re
    body = re.sub(r"^(hey|hi|hello)[^\n]*,?\s*\n+", "", body, flags=re.IGNORECASE)

    # --- Remove emojis from the body ---
    body = re.sub(r"[^\w\s,.!?@%&:;\"'()\[\]\-\/\n]", "", body)

    # --- Remove numbered/bullet formatting at the start of lines ---
    body = re.sub(r"^\s*[\-\*\d]+\s*[:.\)]\s*", "", body, flags=re.MULTILINE)

    # --- Split into short paragraphs (1–2 sentences per paragraph) ---
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    paragraphs = []
    current = ""
    for line in lines:
        if current:
            current += " " + line
        else:
            current = line
        # If the line ends with a period/question mark/exclamation, treat as paragraph end
        if current and current[-1] in ".!?":
            paragraphs.append(current.strip())
            current = ""
    if current:
        paragraphs.append(current.strip())
    body = "\n\n".join(paragraphs)

    # --- Add greeting at the top ---
    if recipient_name and recipient_name.strip().lower() not in ["", "none"]:
        greeting = f"Hey {recipient_name.strip()},"
    elif company and company.strip():
        greeting = f"Hey {company.strip()},"
    elif website and website.strip():
        domain = re.sub(r"https?://(www\.)?", "", website.strip(), flags=re.IGNORECASE)
        domain = domain.split("/")[0]
        greeting = f"Hey {domain},"
    else:
        greeting = "Hey there,"

    body = f"{greeting}\n\n{body}"

    if "stop" not in body.lower():
        body += "\n\nIf this isn't for you, just reply STOP."

    return subject, body

# ----------------------------
# 📤 Send Email
# ----------------------------
def send_email(to_email, to_name, subject, body):
    email_data = sib_api_v3_sdk.SendSmtpEmail(
        to=[{"email": to_email, "name": to_name}],
        sender={"email": SENDER_EMAIL, "name": SENDER_NAME},
        subject=subject,
        html_content=body.replace("\n", "<br>")
    )
    return email_api.send_transac_email(email_data)

def upsert_hubspot_contact(email, firstname, lastname, company, website, keywords):
    url = "https://api.hubapi.com/crm/v3/objects/contacts"
    headers = {
        "Authorization": f"Bearer {HUBSPOT_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "properties": {
            "email": email,
            "firstname": firstname,
            "lastname": lastname,
            "company": company,
            "website": website
            # "notes": keywords  # <-- REMOVE THIS LINE
        }
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 409:  # Contact exists, update it
        # Find contact ID
        search_url = "https://api.hubapi.com/crm/v3/objects/contacts/search"
        search_data = {
            "filterGroups": [{
                "filters": [{
                    "propertyName": "email",
                    "operator": "EQ",
                    "value": email
                }]
            }]
        }
        search_resp = requests.post(search_url, headers=headers, json=search_data)
        if search_resp.ok:
            results = search_resp.json().get("results", [])
            if results:
                contact_id = results[0]["id"]
                update_url = f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}"
                requests.patch(update_url, headers=headers, json={"properties": data["properties"]})
    return response

def add_hubspot_note(email, subject, body):
    # Find contact by email
    search_url = "https://api.hubapi.com/crm/v3/objects/contacts/search"
    headers = {
        "Authorization": f"Bearer {HUBSPOT_TOKEN}",
        "Content-Type": "application/json"
    }
    search_data = {
        "filterGroups": [{
            "filters": [{
                "propertyName": "email",
                "operator": "EQ",
                "value": email
            }]
        }]
    }
    search_resp = requests.post(search_url, headers=headers, json=search_data)
    if search_resp.ok:
        results = search_resp.json().get("results", [])
        if results:
            contact_id = results[0]["id"]
            # Create note with correct association structure
            note_url = "https://api.hubapi.com/crm/v3/objects/notes"
            note_data = {
                "properties": {
                    "hs_note_body": f"Subject: {subject}\n\n{body}"
                },
                "associations": {
                    "contactIds": [contact_id]
                }
            }
            note_resp = requests.post(note_url, headers=headers, json=note_data)
            if not note_resp.ok:
                print("Failed to create note:", note_resp.status_code, note_resp.text)
            else:
                print("Note created:", note_resp.json())
        else:
            print("Contact not found for note association.")
    else:
        print("Failed to search contact for note:", search_resp.status_code, search_resp.text)

def add_to_schedule(email_type, send_time, company, website, email, keywords, name, subject=None, body=None):
    """
    Placeholder function for scheduling emails.
    In production, this should add the email to a database, queue, or scheduling system.
    For now, it just prints the scheduled email.
    """
    print(f"Scheduled {email_type} email to {email} at {send_time}")
    print(f"Company: {company}, Website: {website}, Name: {name}, Keywords: {keywords}")
    if subject:
        print(f"Subject: {subject}")
    if body:
        print(f"Body: {body[:100]}...")  # Print first 100 chars

def process_tracking_and_schedule_followups(tracking_df, leads_df, days_delay=2):
    """Schedule advanced follow-ups based on open tracking."""
    tracking = tracking_df

    # Use 'st_text' column for open detection (case-insensitive, e.g. "Opened", "First open")
    opened_emails = set(tracking[tracking['st_text'].str.contains('open', case=False, na=False)]['email'])
    all_emails = set(leads_df['email'])
    not_opened_emails = all_emails - opened_emails

    # Schedule for opened (but not replied)
    for email in opened_emails:
        row = leads_df[leads_df['email'] == email]
        if row.empty:
            continue
        row = row.iloc[0]
        company = str(row.get("co_name", "")).strip()
        website = str(row.get("website", "")).strip()
        keywords = str(row.get("keywords", "")).strip()
        name = str(row.get("Name", company)).strip()
        prev_subject, prev_body = generate_email(company, website, keywords, name)
        # Schedule a highly personalized follow-up
        send_time = (datetime.now() + timedelta(days=days_delay)).isoformat()
        add_to_schedule("followup", send_time, company, website, email, keywords, name, prev_subject, prev_body)

    # Schedule for not opened
    for email in not_opened_emails:
        row = leads_df[leads_df['email'] == email]
        if row.empty:
            continue
        row = row.iloc[0]
        company = str(row.get("co_name", "")).strip()
        website = str(row.get("website", "")).strip()
        keywords = str(row.get("keywords", "")).strip()
        name = str(row.get("Name", company)).strip()
        # Generate a new subject and body with a different hook
        prev_subject, prev_body = generate_email(company, website, keywords, name)
        send_time = (datetime.now() + timedelta(days=days_delay)).isoformat()
        add_to_schedule("initial", send_time, company, website, email, keywords, name)

# ----------------------------
# 🖥️ Streamlit UI
# ----------------------------
st.set_page_config(page_title="Converzia", layout="wide")
st.title("📬 Converzia: Cold Email Automation")
st.markdown("Upload your lead CSV and let AI generate and send personalized cold emails.")

# --- Add Quick Access Buttons ---
col1, col2 = st.columns(2)
with col1:
    st.markdown(
        '<a href="https://app-smtp.brevo.com/statistics" target="_blank">'
        '<button style="background-color:#2563eb;color:white;padding:8px 18px;border:none;border-radius:5px;font-size:16px;cursor:pointer;">📊 Statistics</button>'
        '</a>',
        unsafe_allow_html=True
    )
with col2:
    st.markdown(
        '<a href="https://www.hubspot.com/" target="_blank">'
        '<button style="background-color:#10b981;color:white;padding:8px 18px;border:none;border-radius:5px;font-size:16px;cursor:pointer;">🗂️ CRM (HubSpot)</button>'
        '</a>',
        unsafe_allow_html=True
    )

file = st.file_uploader("📁 Upload CSV (with columns: co_name, website, email, keywords, Name)", type="csv")

if file:
    df = pd.read_csv(file)
    st.success(f"Loaded {len(df)} leads from file.")

    start = st.number_input("Start index", 0, len(df)-1, value=0)
    end = st.number_input("End index", start+1, len(df), value=min(len(df), start+10))

    if st.button("🚀 Start Sending Emails"):
        skipped = []
        total = end - start
        sent_count = 0
        progress = st.progress(0)
        status_text = st.empty()
        time_per_email = 1.5  # seconds per email (adjust if needed)
        start_time = time.time()

        for idx, i in enumerate(range(start, end), 1):
            row = df.iloc[i]
            company = str(row.get("co_name", "")).strip()
            website = str(row.get("website", "")).strip()
            email = str(row.get("email", "")).strip()
            keywords = str(row.get("keywords", "")).strip()
            name = str(row.get("Name", company)).strip()

            if not email or not is_valid_email_address(email):
                skipped.append((i, email, "Invalid email"))
                continue

            st.markdown(f"#### ✉️ Sending to {name} ({email})")

            try:
                subject, body = generate_email(company, website, keywords, name)
                st.code(f"Subject: {subject}", language="text")
                st.code(body, language="markdown")

                send_email(email, name, subject, body)

                # --- HubSpot Integration ---
                first_name = name.split()[0] if name else ""
                last_name = " ".join(name.split()[1:]) if len(name.split()) > 1 else ""
                upsert_hubspot_contact(email, first_name, last_name, company, website, keywords)
                add_hubspot_note(email, subject, body)
                # --- End HubSpot Integration ---

                sent_count += 1
                elapsed = time.time() - start_time
                emails_left = total - sent_count
                est_time_left = emails_left * time_per_email
                status_text.info(
                    f"Sent: {sent_count}/{total} | Left: {emails_left} | "
                    f"Estimated time left: {int(est_time_left)}s"
                )
                progress.progress(sent_count / total)
                st.success(f"✅ Sent to {email}")
            except ApiException as e:
                st.error(f"❌ Brevo API Error: {e}")
                skipped.append((i, email, "Brevo error"))
            except Exception as e:
                st.error(f"❌ AI/General Error: {e}")
                skipped.append((i, email, "General error"))

            time.sleep(time_per_email)  # avoid rate limits

        st.balloons()
        st.success("✅ All emails processed!")

        if skipped:
            st.warning(f"⚠️ Skipped {len(skipped)} emails.")
            st.dataframe(pd.DataFrame(skipped, columns=["Row", "Email", "Reason"]))
    if st.button("🔁 Send Follow-up Emails"):
        skipped = []
        for i in range(start, end):
            row = df.iloc[i]
            company = str(row.get("co_name", "")).strip()
            website = str(row.get("website", "")).strip()
            email = str(row.get("email", "")).strip()
            keywords = str(row.get("keywords", "")).strip()
            name = str(row.get("Name", company)).strip()



            if not email or not is_valid_email_address(email):
                skipped.append((i, email, "Invalid email"))
                continue

            st.markdown(f"#### 🔁 Sending follow-up to {name} ({email})")

            try:
                # Generate the original email to use as context for the follow-up
                prev_subject, prev_body = generate_email(company, website, keywords)
                subject, body = generate_followup_email(company, website, keywords, prev_subject, prev_body)
                st.code(f"Subject: {subject}", language="text")
                st.code(body, language="markdown")

                send_email(email, name, subject, body)
                upsert_hubspot_contact(email, name, "", company, website, keywords)  # Add contact to HubSpot
                add_hubspot_note(email, subject, body)  # Add note in HubSpot
                st.success(f"✅ Follow-up sent to {email}")
            except ApiException as e:
                st.error(f"❌ Brevo API Error: {e}")
                skipped.append((i, email, "Brevo error"))
            except Exception as e:
                st.error(f"❌ AI/General Error: {e}")
                skipped.append((i, email, "General error"))

            time.sleep(1.5)  # avoid rate limits

        st.balloons()
        st.success("✅ All follow-up emails processed!")

        if skipped:
            st.warning(f"⚠️ Skipped {len(skipped)} emails.")
            st.dataframe(pd.DataFrame(skipped, columns=["Row", "Email", "Reason"]))
else:
    st.info("Please upload a CSV to begin.")

# --- ADVANCED FOLLOW-UP: TRACKING CSV ONLY ---
st.markdown("---")
st.header("📊 Advanced Follow-up: Upload Open/Click Tracking CSV (No Leads CSV Needed)")
tracking_file = st.file_uploader(
    "📊 Upload Open/Click Tracking CSV (columns: st_text, ts, sub, frm, email, tag, mid, link)",
    type="csv",
    key="tracking_csv_only"
)

if tracking_file is not None:
    tracking_df = pd.read_csv(tracking_file)
    st.success(f"Loaded {len(tracking_df)} rows from tracking CSV.")

    st.subheader("Select Range for Advanced Follow-up")
    start_adv = st.number_input(
        "Start index (Advanced Follow-up)", 0, len(tracking_df)-1, value=0, key="start_adv_tracking"
    )
    end_adv = st.number_input(
        "End index (Advanced Follow-up)", start_adv+1, len(tracking_df), value=min(len(tracking_df), start_adv+10), key="end_adv_tracking"
    )

    if st.button("📈 Send Follow-ups Based on Tracking CSV Only"):
        skipped = []
        sent_count = 0
        progress = st.progress(0)
        status_text = st.empty()
        total = end_adv - start_adv
        for idx, i in enumerate(range(start_adv, end_adv), 1):
            row = tracking_df.iloc[i]
            email = str(row.get("email", "")).strip()
            subject_base = str(row.get("sub", "")).strip()
            name = str(row.get("Name", "")).strip()
            if not name:
                name = "there"  # <-- fallback name for Brevo

            if not email or not is_valid_email_address(email):
                skipped.append((i, email, "Invalid email"))
                continue

            prev_subject = subject_base
            prev_body = ""

            subject, body = generate_followup_email("", "", "", prev_subject, prev_body, name)

            st.markdown(f"#### 📧 Sending follow-up to {email}")
            st.code(f"Subject: {subject}", language="text")
            st.code(body, language="markdown")

            try:
                send_email(email, name, subject, body)
                sent_count += 1
                status_text.info(f"Sent: {sent_count}/{total}")
                progress.progress(sent_count / total)
                st.success(f"✅ Sent to {email}")
            except Exception as e:
                st.error(f"❌ Error sending to {email}: {e}")
                skipped.append((i, email, str(e)))
            time.sleep(1.5)  # avoid rate limits

        st.balloons()
        st.success("✅ All advanced follow-up emails processed!")
        if skipped:
            st.warning(f"⚠️ Skipped {len(skipped)} emails.")
            st.dataframe(pd.DataFrame(skipped, columns=["Row", "Email", "Reason"]))