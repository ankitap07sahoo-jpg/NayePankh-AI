import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
KB_PATH = DATA_DIR / "ngo_info.json"


DEFAULT_KNOWLEDGE_BASE = {
    "organization": {
        "name": "NayePankh Foundation",
        "mission": "Empower underserved communities through education, awareness, volunteer action, and social impact programs.",
        "vision": "A society where every child and family can access opportunity, dignity, and support.",
    },
    "programs": [
        {"title": "Education Support", "keywords": ["education", "study", "school", "children"], "answer": "We run educational initiatives, tutoring support, and school supply drives."},
        {"title": "Awareness Campaigns", "keywords": ["campaign", "awareness", "social media", "outreach"], "answer": "We create awareness campaigns for health, education, environment, and community well-being."},
        {"title": "Volunteer Activities", "keywords": ["volunteer", "help", "skills", "support"], "answer": "Volunteers support field work, content, outreach, planning, and community engagement."},
        {"title": "Donation Support", "keywords": ["donate", "fund", "contribute", "money"], "answer": "Donations help us run programs, support campaigns, and expand our community impact."},
    ],
    "faq": [
        {"q": "How can I volunteer?", "keywords": ["volunteer", "join"], "a": "Share your skills, interests, and available hours in the Volunteer Recommender to get matched with a role."},
        {"q": "How can I donate?", "keywords": ["donate", "contribute"], "a": "Use the donation appeal generator or contact the foundation through its official channels to support a cause."},
        {"q": "What skills are required?", "keywords": ["skills", "required"], "a": "Communication, content writing, coordination, design, teaching, and outreach are especially useful."},
        {"q": "What events are available?", "keywords": ["events", "programs"], "a": "Events can include donation drives, awareness programs, school activities, volunteer drives, and campaigns."},
        {"q": "What is NayePankh Foundation?", "keywords": ["what is", "about"], "a": "NayePankh Foundation is an NGO focused on awareness, education, volunteer engagement, and social impact programs."},
    ],
    "contact": {
        "email": "contact@nayepankhfoundation.org",
        "phone": "+91-00000-00000",
        "location": "India",
    },
}


def load_knowledge_base() -> dict[str, Any]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not KB_PATH.exists():
        KB_PATH.write_text(json.dumps(DEFAULT_KNOWLEDGE_BASE, indent=2, ensure_ascii=False), encoding="utf-8")
    return json.loads(KB_PATH.read_text(encoding="utf-8"))


def _keywords(query: str) -> set[str]:
    return {word.strip(".,!?;:").lower() for word in query.split() if len(word) > 2}


def search_knowledge_base(query: str, limit: int = 3) -> list[dict[str, Any]]:
    kb = load_knowledge_base()
    query_terms = _keywords(query)
    candidates: list[dict[str, Any]] = []
    query_text = query.lower()

    organization = kb["organization"]
    candidates.append(
        {
            "title": "Organization Overview",
            "answer": f"{organization['name']} works to {organization['mission']} Vision: {organization['vision']}",
            "score": len(query_terms & {"foundation", "ngo", "mission", "vision", "about", "who", "what"}) + (1 if any(term in query_text for term in ["about", "mission", "vision", "foundation", "ngo"]) else 0),
        }
    )
    for section in kb.get("programs", []):
        score = len(query_terms & set(section["keywords"]))
        candidates.append({"title": section["title"], "answer": section["answer"], "score": score})
    for faq in kb.get("faq", []):
        score = len(query_terms & set(faq["keywords"]))
        candidates.append({"title": faq["q"], "answer": faq["a"], "score": score})

    contact = kb.get("contact", {})
    if contact:
        candidates.append(
            {
                "title": "Contact Information",
                "answer": f"Email: {contact.get('email', 'Not available')}; Phone: {contact.get('phone', 'Not available')}; Location: {contact.get('location', 'Not available')}.",
                "score": len(query_terms & {"contact", "email", "phone", "location", "reach", "connect"}),
            }
        )

    candidates.sort(key=lambda item: item["score"], reverse=True)
    return [item for item in candidates[:limit] if item["score"] > 0] or candidates[:1]


def build_knowledge_context(query: str) -> str:
    hits = search_knowledge_base(query)
    lines = []
    for hit in hits:
        lines.append(f"- {hit['title']}: {hit['answer']}")
    return "\n".join(lines)
