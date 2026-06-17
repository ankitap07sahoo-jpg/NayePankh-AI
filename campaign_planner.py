from typing import Any

from utils import extract_json, safe_gemini_response


SYSTEM_PROMPT = """You are an NGO campaign strategist.
Return valid JSON with keys:
campaign_strategy {title, summary},
target_audience_analysis,
volunteer_requirements,
social_media_plan,
awareness_activities,
risk_assessment,
success_metrics,
expected_impact.
The tone must be professional and actionable.
"""


def _fallback_plan(campaign_name: str, campaign_goal: str, target_audience: str, duration: str, budget: str) -> dict[str, Any]:
    return {
        "campaign_strategy": {
            "title": campaign_name or "Campaign Strategy",
            "summary": campaign_goal or "Build awareness, mobilize volunteers, and generate support.",
        },
        "target_audience_analysis": [
            f"Primary audience: {target_audience or 'Community supporters'}",
            f"Campaign duration: {duration or 'Flexible'}",
        ],
        "volunteer_requirements": [
            "Content and social media support",
            "Outreach and coordination support",
            "Event execution support",
        ],
        "social_media_plan": [
            "Launch announcement post",
            "Mid-campaign progress updates",
            "Final impact recap and thank-you post",
        ],
        "awareness_activities": [
            "Community outreach",
            "Partner engagement",
            "Volunteer activation",
        ],
        "risk_assessment": [
            "Limited response from target audience",
            "Content fatigue",
            "Budget constraint",
        ],
        "success_metrics": [
            "Reach",
            "Engagement",
            "Volunteer sign-ups",
            "Donations or conversions",
        ],
        "expected_impact": [
            "Improved awareness",
            "Stronger volunteer participation",
            "Higher community trust",
        ],
    }


def build_campaign_plan(campaign_name: str, campaign_goal: str, target_audience: str, duration: str, budget: int | float) -> dict[str, Any]:
    prompt = f"""
Campaign name: {campaign_name}
Campaign goal: {campaign_goal}
Target audience: {target_audience}
Duration: {duration}
Budget: {budget}
"""
    try:
        text = safe_gemini_response(prompt, SYSTEM_PROMPT, json_mode=True)
        return extract_json(text)
    except Exception:
        return _fallback_plan(campaign_name, campaign_goal, target_audience, duration, str(budget))
