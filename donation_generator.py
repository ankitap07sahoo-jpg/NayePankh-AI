from utils import safe_gemini_response


SYSTEM_PROMPT = """You are a fundraising copywriter for an NGO.
Return concise but persuasive donation appeal content with sections:
appeal, social_media_content, email_draft, short_message.
"""


def _fallback_appeal(cause: str, target_amount: str, audience: str, tone: str) -> dict[str, str]:
    return {
        "appeal": f"Help us support {cause}. We are aiming to raise {target_amount} from {audience}. Tone: {tone}.",
        "social_media_content": f"Stand with NayePankh Foundation to support {cause}. Every contribution brings us closer to our goal of {target_amount}.",
        "email_draft": f"Dear supporter, we invite you to help us raise {target_amount} for {cause}. Your support will create lasting impact.",
        "short_message": f"Support {cause} with NayePankh Foundation today.",
    }


def generate_donation_appeal(cause: str, target_amount: str, audience: str, tone: str) -> dict[str, str]:
    prompt = f"""
Cause: {cause}
Target amount: {target_amount}
Audience: {audience}
Tone: {tone}
"""
    try:
        import json

        text = safe_gemini_response(prompt, SYSTEM_PROMPT, json_mode=True)
        return json.loads(text)
    except Exception:
        return _fallback_appeal(cause, target_amount, audience, tone)
