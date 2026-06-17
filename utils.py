import json
import os
import re
import time
import uuid
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

import streamlit as st


BASE_DIR = Path(__file__).resolve().parent
EXPORT_DIR = BASE_DIR / "exports"


def load_env() -> None:
    load_dotenv(BASE_DIR / ".env")


def get_session_id() -> str:
    if "session_id" not in st.session_state:
        st.session_state.session_id = f"np-{uuid.uuid4().hex[:12]}"
    return st.session_state.session_id


def format_dt(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M")


def get_user_name_from_memory() -> str:
    return st.session_state.get("memory", {}).get("name", "")


def inject_custom_css() -> None:
    st.markdown(
        """
        <style>
        .hero {
            padding: 1.5rem;
            border-radius: 18px;
            background: linear-gradient(135deg, #0f766e, #134e4a);
            color: white;
            margin-bottom: 1rem;
        }
        .kpi-card {
            padding: 1rem;
            border-radius: 16px;
            background: white;
            border: 1px solid rgba(15, 118, 110, 0.15);
            box-shadow: 0 8px 24px rgba(15, 118, 110, 0.08);
            text-align: center;
            min-height: 120px;
        }
        .kpi-icon { font-size: 1.5rem; margin-bottom: 0.4rem; }
        .kpi-label { font-size: 0.85rem; color: #475569; }
        .kpi-value { font-size: 1.8rem; font-weight: 700; color: #0f766e; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def extract_json(text: str) -> dict[str, Any]:
    match = re.search(r"\{.*\}", text, flags=re.S)
    if not match:
        raise ValueError("JSON object not found in model response")
    return json.loads(match.group(0))


def build_text_report(title: str, payload: Any) -> str:
    return f"{title}\n\n{json.dumps(payload, indent=2, ensure_ascii=False)}\n"


def build_pdf_bytes(title: str, payload: Any) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 48
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(40, y, title)
    y -= 28
    pdf.setFont("Helvetica", 10)
    text = pdf.beginText(40, y)
    for line in build_text_report(title, payload).splitlines():
        if text.getY() < 48:
            pdf.drawText(text)
            pdf.showPage()
            text = pdf.beginText(40, height - 48)
            text.setFont("Helvetica", 10)
        text.textLine(line[:110])
    pdf.drawText(text)
    pdf.save()
    return buffer.getvalue()


def build_download_files(title: str, payload: Any, file_type: str = "txt") -> bytes:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    if file_type == "pdf":
        return build_pdf_bytes(title, payload)
    return build_text_report(title, payload).encode("utf-8")


def safe_gemini_response(prompt: str, system_instruction: str = "", json_mode: bool = False) -> str:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured in the environment")

    import google.generativeai as genai

    genai.configure(api_key=api_key)
    model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    model = genai.GenerativeModel(model_name=model_name, system_instruction=system_instruction or None)
    generation_config = {"temperature": 0.6}
    if json_mode:
        generation_config["response_mime_type"] = "application/json"
    response = model.generate_content(prompt, generation_config=generation_config)
    text = getattr(response, "text", "") or ""
    if not text:
        raise RuntimeError("Gemini returned an empty response")
    return text.strip()


def coerce_list(value: str) -> list[str]:
    items = [item.strip() for item in re.split(r"[,;\n]", value or "") if item.strip()]
    return items


def sleep_progressively(text: str, delay: float = 0.004, cap: float = 1.5) -> None:
    time.sleep(min(cap, len(text) * delay))
