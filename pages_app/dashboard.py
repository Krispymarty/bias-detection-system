"""
FairSight AI — Dashboard Page
Metrics cards, line chart, bar chart, activity feed, and quick actions.
"""
import streamlit as st
from components.cards import metric_card, section_header
from components.charts import fairness_trend_chart, bias_distribution_chart
from utils.mock_data import get_dashboard_metrics, get_activity_feed


def render():
    # Header
    st.markdown(
        """
        <div style="margin-bottom:1.5rem;">
            <h1 style="font-size:1.8rem;font-weight:700;color:white;margin-bottom:0.3rem;">
                📊 Dashboard
            </h1>
            <p style="color:rgba(255,255,255,0.5);font-size:0.9rem;">
                Overview of your AI fairness metrics and analysis
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Metric Cards ──
    metrics = get_dashboard_metrics()
    cols = st.columns(4)
    with cols[0]:
        metric_card("📊", "Fairness Score", f"{metrics['fairness_score']}%", metrics["fairness_delta"])
    with cols[1]:
        metric_card("⚖️", "Bias Index", f"{metrics['bias_index']}", metrics["bias_delta"], "teal")
    with cols[2]:
        metric_card("🎯", "Accuracy", f"{metrics['accuracy']}%", metrics["accuracy_delta"])
    with cols[3]:
        metric_card("🔬", "Models Analyzed", f"{metrics['models_analyzed']:,}", metrics["models_delta"])

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts + Activity ──
    chart_col, activity_col = st.columns([2, 1])

    with chart_col:
        st.plotly_chart(
            fairness_trend_chart(), use_container_width=True, config={"displayModeBar": False}
        )
        st.plotly_chart(
            bias_distribution_chart(), use_container_width=True, config={"displayModeBar": False}
        )

    with activity_col:
        activities = get_activity_feed()
        type_colors = {
            "success": "#00FFD1",
            "warning": "#FFD700",
            "info": "rgba(255,255,255,0.45)",
        }

        items_html = ""
        for act in activities:
            color = type_colors.get(act["type"], "rgba(255,255,255,0.45)")
            items_html += f"""
            <div style="display:flex;gap:0.8rem;align-items:flex-start;padding:0.7rem 0;
                        border-bottom:1px solid rgba(255,255,255,0.04);">
                <span style="font-size:1.15rem;flex-shrink:0;">{act['icon']}</span>
                <div style="flex:1;min-width:0;">
                    <div style="font-size:0.82rem;color:rgba(255,255,255,0.75);
                                line-height:1.4;">{act['action']}</div>
                    <div style="font-size:0.72rem;color:{color};margin-top:0.15rem;">{act['time']}</div>
                </div>
            </div>
            """

        st.markdown(
            f"""
            <div class="glass-card" style="padding:1.5rem;">
                <h3 style="font-size:1rem;font-weight:600;color:white;margin-bottom:1rem;">
                    🕐 Recent Activity
                </h3>
                {items_html}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── Quick Actions ──
    st.markdown("<br>", unsafe_allow_html=True)
    section_header("⚡ QUICK ACTIONS", "Jump Into Action")

    cols = st.columns(4)
    actions = [
        ("🤖", "AI Agent", "Chat with our AI assistant"),
        ("🔬", "What-If", "Run fairness simulations"),
        ("⚙️", "Settings", "Configure your profile"),
        ("❓", "Help", "Get support & answers"),
    ]
    for col, (icon, title, desc) in zip(cols, actions):
        with col:
            st.markdown(
                f"""
                <div class="glass-card glass-card-teal" style="text-align:center;padding:1.5rem;cursor:pointer;">
                    <div style="font-size:2rem;margin-bottom:0.5rem;">{icon}</div>
                    <div style="font-weight:600;color:white;margin-bottom:0.25rem;">{title}</div>
                    <div style="font-size:0.78rem;color:rgba(255,255,255,0.45);">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
