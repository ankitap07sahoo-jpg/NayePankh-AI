import os
from datetime import datetime
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

from analytics import get_dashboard_metrics, get_dashboard_figures
from campaign_planner import build_campaign_plan
from chatbot import generate_chat_response, remember_user_facts
from content_generator import generate_ngo_content
from database import (
    get_chat_history,
    get_recent_campaigns,
    get_recent_content,
    get_recent_volunteer_recommendations,
    get_memory,
    get_user_profile,
    init_db,
    record_app_event,
    save_campaign_plan,
    save_chat_message,
    save_content,
    save_volunteer_recommendation,
    set_memory_value,
)
from donation_generator import generate_donation_appeal
from knowledge_base import load_knowledge_base, search_knowledge_base
from utils import (
    build_download_files,
    format_dt,
    get_session_id,
    get_user_name_from_memory,
    inject_custom_css,
    load_env,
)
from volunteer_recommender import recommend_volunteer_role


APP_TITLE = "NayePankh AI Campaign & Volunteer Assistant"

NAVIGATION = [
    "Home",
    "AI Chat Assistant",
    "Volunteer Recommender",
    "Content Generator",
    "Campaign Planner",
    "Donation Appeal Generator",
    "Analytics Dashboard",
    "About Project",
]


def init_app_state() -> None:
    st.session_state.setdefault("session_id", get_session_id())
    st.session_state.setdefault("generated_outputs", {})
    persisted_memory = get_memory(st.session_state.session_id)
    profile = get_user_profile(st.session_state.session_id)
    merged_memory = dict(st.session_state.get("memory", {}))
    merged_memory.update(persisted_memory)
    merged_memory.update({key: value for key, value in profile.items() if value})
    st.session_state.memory = merged_memory
    st.session_state.current_user_name = merged_memory.get("name", profile.get("name", ""))
    if "messages" not in st.session_state or not st.session_state.messages:
        st.session_state.messages = get_chat_history(st.session_state.session_id)


def set_page_config() -> None:
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="🤝",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def sidebar() -> str:
    with st.sidebar:
        st.markdown("## 🤝 NayePankh AI")
        st.caption("NGO productivity platform")
        page = st.radio("Navigate", NAVIGATION, label_visibility="collapsed")
        st.markdown("---")
        st.markdown("### Session")
        st.write(f"ID: `{st.session_state.session_id}`")
        if st.session_state.get("current_user_name"):
            st.write(f"User: **{st.session_state.current_user_name}**")
        st.markdown("---")
        st.caption("Gemini API is used when configured. The app falls back to local intelligence when offline.")
    return page


def kpi_cards(metrics: dict) -> None:
    cols = st.columns(5)
    cards = [
        ("Total Users", metrics.get("total_users", 0), "👥"),
        ("Chat Interactions", metrics.get("total_chat_interactions", 0), "💬"),
        ("Campaigns", metrics.get("total_campaigns", 0), "📣"),
        ("Content Pieces", metrics.get("total_content", 0), "📝"),
        ("Volunteer Requests", metrics.get("total_recommendations", 0), "🙌"),
    ]
    for col, (label, value, icon) in zip(cols, cards):
        with col:
            st.markdown(f"<div class='kpi-card'><div class='kpi-icon'>{icon}</div><div class='kpi-label'>{label}</div><div class='kpi-value'>{value}</div></div>", unsafe_allow_html=True)


def render_home() -> None:
    st.markdown(
        """
        <div class="hero">
            <h1>NayePankh AI Campaign & Volunteer Assistant</h1>
            <p>Plan campaigns, guide volunteers, generate outreach content, and answer NGO questions with local memory plus Gemini intelligence.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    metrics = get_dashboard_metrics()
    kpi_cards(metrics)
    st.markdown("### What this platform does")
    st.write(
        "A real NGO productivity workspace with chat support, volunteer matching, campaign planning, donation appeals, analytics, and export-ready reports."
    )
    cols = st.columns(3)
    with cols[0]:
        st.info("💬 AI chat with retrieval over the local NayePankh knowledge base.")
    with cols[1]:
        st.success("🧭 Volunteer recommendations based on skills, interests, and availability.")
    with cols[2]:
        st.warning("📊 Analytics dashboard for operational visibility and decision-making.")


def render_chat() -> None:
    st.subheader("AI Chat Assistant")
    st.caption("Ask about the foundation, volunteering, donations, programs, events, or your saved memory.")

    history = st.session_state.messages
    for item in history:
        with st.chat_message(item["role"]):
            st.markdown(item["content"])
            if item.get("timestamp"):
                st.caption(item["timestamp"])

    prompt = st.chat_input("Ask NayePankh AI anything...")
    if not prompt:
        return

    user_name = st.session_state.get("current_user_name") or get_user_name_from_memory()
    if not user_name and st.session_state.memory.get("name"):
        user_name = st.session_state.memory["name"]

    remember_user_facts(prompt, st.session_state.memory, st.session_state.session_id)
    if st.session_state.memory.get("name"):
        st.session_state.current_user_name = st.session_state.memory["name"]

    history.append({"role": "user", "content": prompt, "timestamp": format_dt(datetime.now())})
    save_chat_message(
        session_id=st.session_state.session_id,
        user_name=user_name or st.session_state.memory.get("name", ""),
        role="user",
        message=prompt,
        response="",
    )

    knowledge_hits = search_knowledge_base(prompt)
    response = generate_chat_response(
        prompt=prompt,
        session_id=st.session_state.session_id,
        memory=st.session_state.memory,
        knowledge_hits=knowledge_hits,
    )

    with st.chat_message("assistant"):
        placeholder = st.empty()
        rendered = ""
        for token in response.split():
            rendered = f"{rendered} {token}".strip()
            placeholder.markdown(rendered)
        placeholder.markdown(response)

    history.append({"role": "assistant", "content": response, "timestamp": format_dt(datetime.now())})
    save_chat_message(
        session_id=st.session_state.session_id,
        user_name=user_name or st.session_state.memory.get("name", ""),
        role="assistant",
        message=prompt,
        response=response,
    )
    record_app_event(st.session_state.session_id, "chat_interaction", {"prompt": prompt})


def render_volunteer_recommender() -> None:
    st.subheader("Volunteer Role Recommender")
    with st.form("volunteer_form"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Name", value=st.session_state.get("current_user_name", ""))
        skills = c1.text_input("Skills", placeholder="Communication, teaching, design, outreach")
        interests = c2.text_input("Interests", placeholder="Education, women empowerment, health")
        education = c2.text_input("Education", placeholder="Graduate / School / Specialized training")
        hours = st.slider("Available hours per week", 1, 40, 5)
        submitted = st.form_submit_button("Recommend Role")

    if not submitted:
        return

    if name:
        st.session_state.current_user_name = name
        st.session_state.memory["name"] = name
        set_memory_value(st.session_state.session_id, "name", name)

    recommendation = recommend_volunteer_role(
        name=name,
        skills=skills,
        interests=interests,
        education=education,
        available_hours=hours,
    )
    st.session_state.generated_outputs["volunteer"] = recommendation
    save_volunteer_recommendation(
        session_id=st.session_state.session_id,
        user_name=name,
        request_json={
            "name": name,
            "skills": skills,
            "interests": interests,
            "education": education,
            "available_hours": hours,
        },
        response_json=recommendation,
    )
    record_app_event(st.session_state.session_id, "volunteer_recommendation", recommendation)
    st.success("Recommendation generated")

    cols = st.columns(2)
    with cols[0]:
        st.markdown(f"### {recommendation['role']}")
        st.markdown(f"**Why this fits:** {recommendation['reason']}")
        st.markdown("**Contribution opportunities**")
        for item in recommendation["contribution_opportunities"]:
            st.markdown(f"- {item}")
    with cols[1]:
        st.markdown("### Suggested activities")
        for item in recommendation["activities"]:
            st.markdown(f"- {item}")
        st.markdown("**Learning opportunities**")
        for item in recommendation["learning_opportunities"]:
            st.markdown(f"- {item}")
    st.download_button(
        "Download recommendation TXT",
        data=build_download_files("volunteer_recommendation", recommendation, file_type="txt"),
        file_name="volunteer_recommendation.txt",
        mime="text/plain",
    )
    st.download_button(
        "Download recommendation PDF",
        data=build_download_files("volunteer_recommendation", recommendation, file_type="pdf"),
        file_name="volunteer_recommendation.pdf",
        mime="application/pdf",
    )


def render_content_generator() -> None:
    st.subheader("AI Content Generator")
    with st.form("content_form"):
        c1, c2 = st.columns(2)
        content_type = c1.selectbox(
            "Content type",
            [
                "Instagram Post",
                "LinkedIn Post",
                "Donation Appeal",
                "Awareness Campaign Content",
                "Volunteer Recruitment Message",
                "Event Announcement",
                "Email Campaign",
            ],
        )
        topic = c1.text_input("Topic", placeholder="Back-to-school drive")
        audience = c2.text_input("Audience", placeholder="Donors, students, parents, corporate CSR teams")
        tone = c2.selectbox("Tone", ["Professional", "Warm", "Inspirational", "Urgent", "Friendly"])
        submitted = st.form_submit_button("Generate Content")

    if not submitted:
        return

    output = generate_ngo_content(content_type=content_type, topic=topic, audience=audience, tone=tone)
    st.session_state.generated_outputs["content"] = output
    save_content(
        session_id=st.session_state.session_id,
        user_name=st.session_state.get("current_user_name", ""),
        content_type=content_type,
        topic=topic,
        audience=audience,
        tone=tone,
        content=output,
    )
    record_app_event(st.session_state.session_id, "content_generated", {"type": content_type, "topic": topic})
    st.success("Content generated")
    st.markdown(output)
    st.download_button(
        "Download as TXT",
        data=build_download_files("content", output, file_type="txt"),
        file_name="ngo_content.txt",
        mime="text/plain",
    )
    st.download_button(
        "Download as PDF",
        data=build_download_files("content", output, file_type="pdf"),
        file_name="ngo_content.pdf",
        mime="application/pdf",
    )


def render_campaign_planner() -> None:
    st.subheader("AI Campaign Planner")
    with st.form("campaign_form"):
        c1, c2 = st.columns(2)
        campaign_name = c1.text_input("Campaign name", placeholder="Education for Every Child")
        campaign_goal = c1.text_area("Campaign goal", height=100, placeholder="Raise awareness and funds for school kits.")
        target_audience = c2.text_input("Target audience", placeholder="Donors, volunteers, schools, CSR partners")
        duration = c2.text_input("Campaign duration", placeholder="4 weeks")
        budget = st.number_input("Budget (INR)", min_value=0, value=50000, step=1000)
        submitted = st.form_submit_button("Generate Campaign Plan")

    if not submitted:
        return

    plan = build_campaign_plan(
        campaign_name=campaign_name,
        campaign_goal=campaign_goal,
        target_audience=target_audience,
        duration=duration,
        budget=budget,
    )
    st.session_state.generated_outputs["campaign"] = plan
    save_campaign_plan(
        session_id=st.session_state.session_id,
        user_name=st.session_state.get("current_user_name", ""),
        campaign_name=campaign_name,
        goal=campaign_goal,
        target_audience=target_audience,
        duration=duration,
        budget=str(budget),
        report_json=plan,
    )
    record_app_event(st.session_state.session_id, "campaign_generated", {"name": campaign_name})
    st.success("Campaign plan generated")
    st.markdown(f"## {plan['campaign_strategy']['title']}")
    st.markdown(plan["campaign_strategy"]["summary"])

    sections = [
        ("Target Audience Analysis", plan["target_audience_analysis"]),
        ("Volunteer Requirements", plan["volunteer_requirements"]),
        ("Social Media Plan", plan["social_media_plan"]),
        ("Awareness Activities", plan["awareness_activities"]),
        ("Risk Assessment", plan["risk_assessment"]),
        ("Success Metrics", plan["success_metrics"]),
        ("Expected Impact", plan["expected_impact"]),
    ]
    for title, data in sections:
        st.markdown(f"### {title}")
        if isinstance(data, list):
            for item in data:
                st.markdown(f"- {item}")
        elif isinstance(data, dict):
            for key, value in data.items():
                st.markdown(f"- **{key}**: {value}")
        else:
            st.write(data)

    st.download_button(
        "Download campaign plan TXT",
        data=build_download_files("campaign", plan, file_type="txt"),
        file_name="campaign_plan.txt",
        mime="text/plain",
    )
    st.download_button(
        "Download campaign plan PDF",
        data=build_download_files("campaign", plan, file_type="pdf"),
        file_name="campaign_plan.pdf",
        mime="application/pdf",
    )


def render_donation_generator() -> None:
    st.subheader("Donation Appeal Generator")
    with st.form("donation_form"):
        c1, c2 = st.columns(2)
        cause = c1.text_input("Cause", placeholder="School supplies for rural children")
        target_amount = c1.text_input("Target amount", placeholder="INR 250000")
        audience = c2.text_input("Audience", placeholder="Individual donors, CSR teams, alumni")
        tone = c2.selectbox("Tone", ["Emotional", "Professional", "Urgent", "Hopeful"])
        submitted = st.form_submit_button("Generate Appeal")

    if not submitted:
        return

    output = generate_donation_appeal(cause=cause, target_amount=target_amount, audience=audience, tone=tone)
    st.session_state.generated_outputs["donation"] = output
    record_app_event(st.session_state.session_id, "donation_appeal_generated", {"cause": cause})
    st.success("Donation appeal generated")
    st.markdown(f"### Appeal")
    st.markdown(output["appeal"])
    st.markdown("### Social Media Content")
    st.markdown(output["social_media_content"])
    st.markdown("### Email Draft")
    st.markdown(output["email_draft"])
    st.markdown("### Short Fundraising Message")
    st.markdown(output["short_message"])
    st.download_button(
        "Download appeal TXT",
        data=build_download_files("donation", output, file_type="txt"),
        file_name="donation_appeal.txt",
        mime="text/plain",
    )
    st.download_button(
        "Download appeal PDF",
        data=build_download_files("donation", output, file_type="pdf"),
        file_name="donation_appeal.pdf",
        mime="application/pdf",
    )


def render_analytics() -> None:
    st.subheader("Admin Analytics Dashboard")
    metrics = get_dashboard_metrics()
    kpi_cards(metrics)
    figures = get_dashboard_figures()
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(figures["activity"], use_container_width=True)
    with c2:
        st.plotly_chart(figures["content_types"], use_container_width=True)
    st.plotly_chart(figures["campaigns"], use_container_width=True)


def render_about() -> None:
    st.subheader("About Project")
    st.markdown(
        """
        **NayePankh AI Campaign & Volunteer Assistant** is designed as an NGO productivity platform.

        It combines:
        - AI chat with local knowledge retrieval
        - volunteer role recommendations
        - content generation for campaigns and fundraising
        - campaign planning workflows
        - persistent memory and analytics
        - PDF/TXT export support
        """
    )
    st.markdown("### Deployment guide")
    st.code("streamlit run app.py", language="bash")


def main() -> None:
    load_env()
    init_db()
    init_app_state()
    inject_custom_css()
    load_knowledge_base()
    page = sidebar()

    st.title(APP_TITLE)
    st.caption("AI-powered NGO operations assistant for NayePankh Foundation")

    if page == "Home":
        render_home()
    elif page == "AI Chat Assistant":
        render_chat()
    elif page == "Volunteer Recommender":
        render_volunteer_recommender()
    elif page == "Content Generator":
        render_content_generator()
    elif page == "Campaign Planner":
        render_campaign_planner()
    elif page == "Donation Appeal Generator":
        render_donation_generator()
    elif page == "Analytics Dashboard":
        render_analytics()
    elif page == "About Project":
        render_about()


if __name__ == "__main__":
    main()
