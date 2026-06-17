from collections import Counter
import json

import plotly.graph_objects as go

from database import get_connection, get_statistics


def get_dashboard_metrics() -> dict[str, int]:
    return get_statistics()


def get_dashboard_figures() -> dict[str, go.Figure]:
    conn = get_connection()
    events = conn.execute("SELECT event_type, COUNT(*) AS count FROM app_events GROUP BY event_type").fetchall()
    content = conn.execute("SELECT content_type, COUNT(*) AS count FROM generated_content GROUP BY content_type").fetchall()
    campaigns = conn.execute("SELECT date(created_at) AS day, COUNT(*) AS count FROM campaigns GROUP BY date(created_at) ORDER BY day").fetchall()
    conn.close()

    activity_fig = go.Figure(
        data=[go.Bar(x=[row["event_type"] for row in events] or ["None"], y=[row["count"] for row in events] or [0], marker_color="#0f766e")]
    )
    activity_fig.update_layout(title="Platform Activity", height=340, margin=dict(l=20, r=20, t=50, b=20))

    content_fig = go.Figure(
        data=[go.Pie(labels=[row["content_type"] for row in content] or ["None"], values=[row["count"] for row in content] or [1], hole=0.45)]
    )
    content_fig.update_layout(title="Content Mix", height=340, margin=dict(l=20, r=20, t=50, b=20))

    campaigns_fig = go.Figure(
        data=[go.Scatter(x=[row["day"] for row in campaigns] or ["No data"], y=[row["count"] for row in campaigns] or [0], mode="lines+markers", line=dict(color="#134e4a"))]
    )
    campaigns_fig.update_layout(title="Campaigns Over Time", height=340, margin=dict(l=20, r=20, t=50, b=20))

    return {"activity": activity_fig, "content_types": content_fig, "campaigns": campaigns_fig}
