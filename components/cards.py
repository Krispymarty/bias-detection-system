"""
FairSight AI — Reusable Card Components
Glassmorphism-styled HTML card renderers for Streamlit.
"""
import streamlit as st


def glass_card(content, extra_class=""):
    """Render a glassmorphism card with arbitrary HTML content."""
    st.markdown(
        f'<div class="glass-card {extra_class}">{content}</div>',
        unsafe_allow_html=True,
    )


def metric_card(icon, label, value, delta=None, delta_color="teal"):
    """Dashboard metric card with icon, label, value, and optional delta."""
    delta_html = ""
    if delta is not None:
        sign = "+" if delta > 0 else ""
        color_map = {"teal": "#00FFD1", "red": "#FF5050", "yellow": "#FFD700"}
        color = color_map.get(delta_color, "#00FFD1")
        arrow = "↑" if delta > 0 else "↓"
        delta_html = (
            f'<div style="font-size:0.8rem;color:{color};font-weight:500;'
            f'margin-top:0.3rem;">{arrow} {sign}{delta}</div>'
        )

    st.markdown(
        f"""
        <div class="glass-card glass-card-teal" style="padding:1.5rem;text-align:center;">
            <div style="font-size:1.8rem;margin-bottom:0.5rem;">{icon}</div>
            <div style="font-size:0.75rem;color:rgba(255,255,255,0.45);text-transform:uppercase;
                        letter-spacing:0.1em;font-weight:600;margin-bottom:0.4rem;">{label}</div>
            <div class="stat-number" style="font-size:2rem;margin-bottom:0;">{value}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def feature_card(icon, title, description):
    """Feature highlight card with icon, title, and description."""
    st.markdown(
        f"""
        <div class="glass-card glass-card-teal" style="padding:1.5rem;height:100%;">
            <div class="feature-icon" style="margin-bottom:1rem;">{icon}</div>
            <h3 style="font-size:1.1rem;font-weight:600;color:white;margin-bottom:0.5rem;">{title}</h3>
            <p style="font-size:0.88rem;color:rgba(255,255,255,0.55);line-height:1.65;margin:0;">{description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def team_card(emoji, name, role):
    """Team member card with avatar emoji, name, and role."""
    st.markdown(
        f"""
        <div class="glass-card" style="text-align:center;padding:2rem 1.5rem;">
            <div class="avatar-placeholder" style="margin-bottom:1rem;">{emoji}</div>
            <h4 style="font-size:1rem;font-weight:600;color:white;margin-bottom:0.3rem;">{name}</h4>
            <p style="font-size:0.82rem;color:rgba(255,255,255,0.45);margin:0;">{role}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def stat_card(number, label):
    """Statistics card with big number and label."""
    st.markdown(
        f"""
        <div style="text-align:center;padding:1rem 0.5rem;">
            <div class="stat-number">{number}</div>
            <div class="stat-label">{label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def result_card(title, value, status="positive"):
    """Result card for the What-If simulator."""
    status_colors = {"positive": "#00FFD1", "caution": "#FFD700", "negative": "#FF5050"}
    color = status_colors.get(status, "#00FFD1")
    st.markdown(
        f"""
        <div class="result-card {status}">
            <div style="font-size:0.75rem;color:rgba(255,255,255,0.45);text-transform:uppercase;
                        letter-spacing:0.08em;font-weight:600;margin-bottom:0.4rem;">{title}</div>
            <div style="font-size:1.8rem;font-weight:700;color:{color};">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def step_card(number, icon, title, description):
    """Tutorial step card with number badge, icon, title, and description."""
    st.markdown(
        f"""
        <div class="glass-card" style="display:flex;gap:1.5rem;align-items:flex-start;padding:1.5rem;">
            <div class="step-number">{number}</div>
            <div style="flex:1;">
                <div style="font-size:1.5rem;margin-bottom:0.3rem;">{icon}</div>
                <h3 style="font-size:1.1rem;font-weight:600;color:white;margin-bottom:0.5rem;">{title}</h3>
                <p style="font-size:0.88rem;color:rgba(255,255,255,0.55);line-height:1.65;margin:0;">{description}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(badge_text, title, subtitle=""):
    """Section header with teal badge, title, and optional subtitle."""
    subtitle_html = ""
    if subtitle:
        subtitle_html = (
            f'<p style="font-size:1rem;color:rgba(255,255,255,0.55);max-width:600px;'
            f'margin:0.5rem auto 0;line-height:1.65;">{subtitle}</p>'
        )
    st.markdown(
        f"""
        <div style="text-align:center;margin-bottom:2rem;">
            <div class="teal-badge" style="margin-bottom:1rem;">{badge_text}</div>
            <h2 style="font-size:2rem;font-weight:700;color:white;margin-bottom:0;">{title}</h2>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def faq_item(question, answer):
    """Render an FAQ item using a Streamlit expander."""
    with st.expander(question):
        st.markdown(
            f'<p style="color:rgba(255,255,255,0.65);line-height:1.7;margin:0;">{answer}</p>',
            unsafe_allow_html=True,
        )
