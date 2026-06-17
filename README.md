# NayePankh AI Campaign & Volunteer Assistant

An AI-powered NGO productivity platform for NayePankh Foundation.

## Features

- AI chat assistant with local knowledge retrieval
- volunteer role recommender
- AI content generation
- multi-step campaign planning
- donation appeal generation
- persistent SQLite memory
- analytics dashboard with Plotly
- TXT/PDF export support
- modern NGO-themed Streamlit UI
- Gemini AI integration with offline fallbacks

## Database Schema

- `users` — saved profile and interest data
- `chat_history` — user/assistant conversation log
- `generated_content` — social, email, and outreach content
- `campaigns` — campaign plans and reports
- `volunteer_recommendations` — volunteer matching results
- `user_memory` — key/value memory for names and preferences
- `app_events` — analytics events

## Project Structure

- `app.py` — Streamlit UI and page routing
- `database.py` — SQLite schema and persistence helpers
- `knowledge_base.py` — local NGO knowledge base and retrieval
- `chatbot.py` — Gemini chat and memory logic
- `volunteer_recommender.py` — volunteer matching engine
- `content_generator.py` — content generation
- `campaign_planner.py` — campaign workflow
- `donation_generator.py` — fundraising copy generation
- `analytics.py` — KPI and Plotly dashboard data
- `utils.py` — shared helpers and export generation

## Setup

1. Create a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create `.env`:
   ```env
   GEMINI_API_KEY=your_key_here
   GEMINI_MODEL=gemini-1.5-flash
   ```
4. Run the app:
   ```bash
   streamlit run app.py
   ```

## Deployment Guide

For Streamlit Community Cloud or any Python host:

1. Push the repo to GitHub.
2. Add `GEMINI_API_KEY` and `GEMINI_MODEL` as secrets/environment variables.
3. Ensure the `data/` and `exports/` folders are writable.
4. Launch with `streamlit run app.py`.
5. Confirm SQLite file creation at `data/app.db` on first run.

## Project Report Summary

This application centralizes NGO operations into one interface: users can ask questions, receive volunteer recommendations, generate outreach content, plan campaigns, create donation appeals, and track usage through analytics. The app stores session memory in SQLite and uses Gemini only where AI generation is needed, with local fallback logic so the platform still works without an API key.

## Technical Notes

- Streamlit `session_state` keeps the live conversation and memory on screen.
- SQLite persists chats, content, campaigns, volunteers, and analytics events.
- Gemini is used for generation; local knowledge base retrieval answers common NGO questions first.
- Plotly dashboards visualize usage across the assistant.
"# NayePankh-AI" 
