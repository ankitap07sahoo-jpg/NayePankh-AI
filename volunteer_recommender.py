from typing import Any

from utils import coerce_list, safe_gemini_response


SYSTEM_PROMPT = """You are a volunteer strategy assistant for an NGO.
Recommend roles that fit the user's background, skills, interests, education, and available hours.
Return a concise professional recommendation in valid JSON with keys:
role, reason, activities, contribution_opportunities, learning_opportunities.
"""


def _fallback_recommendation(name: str, skills: str, interests: str, education: str, available_hours: int) -> dict[str, Any]:
    skill_text = f"{skills} {interests} {education}".lower()
    if any(term in skill_text for term in ["design", "content", "social", "writing", "communication"]):
        role = "Community Content & Outreach Volunteer"
    elif any(term in skill_text for term in ["teach", "education", "school", "training"]):
        role = "Education Support Volunteer"
    elif any(term in skill_text for term in ["event", "coordination", "management", "planning"]):
        role = "Campaign Coordination Volunteer"
    else:
        role = "Community Support Volunteer"
    return {
        "role": role,
        "reason": f"{name or 'You'} match this role based on your skills and availability of {available_hours} hours per week.",
        "activities": [
            "Support awareness or field activities",
            "Coordinate with the team on assigned tasks",
            "Share progress updates and feedback",
        ],
        "contribution_opportunities": [
            "Campaign support",
            "Volunteer onboarding support",
            "Community outreach",
        ],
        "learning_opportunities": [
            "NGO operations exposure",
            "Project coordination practice",
            "Communication and leadership development",
        ],
    }


def recommend_volunteer_role(name: str, skills: str, interests: str, education: str, available_hours: int) -> dict[str, Any]:
    prompt = f"""
Name: {name}
Skills: {skills}
Interests: {interests}
Education: {education}
Available hours per week: {available_hours}
"""
    try:
        text = safe_gemini_response(prompt, SYSTEM_PROMPT, json_mode=True)
        import json

        return json.loads(text)
    except Exception:
        return _fallback_recommendation(name, skills, interests, education, available_hours)
