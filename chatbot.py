import re
from typing import Any

from database import set_memory_value, upsert_user_profile
from knowledge_base import build_knowledge_context
from utils import safe_gemini_response


SYSTEM_PROMPT = """You are the NayePankh Foundation AI assistant.
Answer professionally, warmly, and concisely.
Use the provided foundation knowledge base first.
If a memory fact is present, answer directly from memory.
If the answer is unknown, say so and offer next steps.
"""


def remember_user_facts(message: str, memory: dict[str, str], session_id: str) -> None:
    name_match = re.search(r"\bmy name is ([A-Za-z][A-Za-z\s'.-]{1,50})", message, flags=re.I)
    if name_match:
        name = name_match.group(1).strip().split()[0]
        memory["name"] = name
        set_memory_value(session_id, "name", name)
        upsert_user_profile(session_id, name=name)

    interest_match = re.search(r"\bI am interested in ([A-Za-z0-9,\s-]{3,80})", message, flags=re.I)
    if interest_match:
        interest = interest_match.group(1).strip()
        memory["interests"] = interest
        set_memory_value(session_id, "interests", interest)
        upsert_user_profile(session_id, name=memory.get("name", ""), interests=interest)


def answer_from_memory(message: str, memory: dict[str, str]) -> str | None:
    lower = message.lower()
    if "what is my name" in lower or "tell me my name" in lower:
        return f"Your name is {memory['name']}." if memory.get("name") else "I do not have your name saved yet."
    if "what are my interests" in lower:
        return f"Your interests are {memory['interests']}." if memory.get("interests") else "I do not have your interests saved yet."
    return None


def answer_from_knowledge(message: str, knowledge_hits: list[dict[str, Any]]) -> str | None:
    if not knowledge_hits:
        return None
    lower = message.lower()
    direct_question = any(
        phrase in lower
        for phrase in [
            "what is naye",
            "what is the foundation",
            "how can i volunteer",
            "how can i donate",
            "what programs",
            "what skills",
            "what events",
            "contact",
            "email",
            "phone",
            "mission",
            "vision",
        ]
    )
    if not direct_question and knowledge_hits[0].get("score", 0) < 2:
        return None
    lines = ["Here is the most relevant information from the NayePankh knowledge base:"]
    for hit in knowledge_hits:
        lines.append(f"- {hit['title']}: {hit['answer']}")
    return "\n".join(lines)


def generate_chat_response(prompt: str, session_id: str, memory: dict[str, str], knowledge_hits: list[dict[str, Any]]) -> str:
    memory_answer = answer_from_memory(prompt, memory)
    if memory_answer:
        return memory_answer

    knowledge_answer = answer_from_knowledge(prompt, knowledge_hits)
    if knowledge_answer:
        return knowledge_answer

    context = build_knowledge_context(prompt)
    if knowledge_hits:
        context = "\n".join(f"{hit['title']}: {hit['answer']}" for hit in knowledge_hits)

    prompt_block = f"""
User message:
{prompt}

Memory:
{memory}

Knowledge base context:
{context}

Return a helpful NGO assistant response. If the user is asking about volunteering, donations, programs, or events, answer using the foundation context.
"""
    try:
        return safe_gemini_response(prompt_block, SYSTEM_PROMPT)
    except Exception as exc:
        if context:
            return f"{context}\n\nI could not reach Gemini right now, so I answered from the local knowledge base."
        return f"AI response unavailable: {exc}"
