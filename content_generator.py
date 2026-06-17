from typing import Any

from utils import safe_gemini_response


SYSTEM_PROMPT = """You write polished NGO content.
Produce professional, campaign-ready copy for social media, email, and outreach.
Use the user's chosen tone and audience.
"""


def _fallback_text(content_type: str, topic: str, audience: str, tone: str) -> str:
    return (
        f"**{content_type}**\n\n"
        f"Topic: {topic}\n"
        f"Audience: {audience}\n"
        f"Tone: {tone}\n\n"
        f"Join NayePankh Foundation in creating measurable social impact around {topic}. "
        "Together we can educate, empower, and amplify community action."
    )


def generate_ngo_content(content_type: str, topic: str, audience: str, tone: str) -> str:
    prompt = f"""
Content type: {content_type}
Topic: {topic}
Audience: {audience}
Tone: {tone}
Create a high-quality, ready-to-publish piece of content.
"""
    try:
        return safe_gemini_response(prompt, SYSTEM_PROMPT)
    except Exception:
        return _fallback_text(content_type, topic, audience, tone)
