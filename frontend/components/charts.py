"""
FairSight AI — Plotly Chart Builders
Dark-themed, teal-accented charts for dashboard and simulator.
"""
import plotly.graph_objects as go
from utils.mock_data import get_fairness_trend_data, get_model_distribution


COLORS = {
    "teal": "#00FFD1",
    "teal_dark": "#00CCA6",
    "blue": "#3B82F6",
    "purple": "#8B5CF6",
    "yellow": "#FFD700",
    "red": "#FF5050",
    "text_muted": "rgba(255,255,255,0.3)",
    "grid": "rgba(255,255,255,0.04)",
}


def _base_layout(title="") -> dict:
    """Standard dark transparent layout dict."""
    layout = dict(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="rgba(255,255,255,0.6)", size=12),
        margin=dict(l=40, r=20, t=50 if title else 30, b=40),
        xaxis=dict(
            gridcolor=COLORS["grid"],
            zerolinecolor=COLORS["grid"],
            tickfont=dict(color=COLORS["text_muted"]),
        ),
        yaxis=dict(
            gridcolor=COLORS["grid"],
            zerolinecolor=COLORS["grid"],
            tickfont=dict(color=COLORS["text_muted"]),
        ),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color="rgba(255,255,255,0.55)", size=11),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="#162038",
            font_color="white",
            font_family="Inter, sans-serif",
            bordercolor="rgba(0,255,209,0.2)",
        ),
    )
    if title:
        layout["title"] = dict(text=title, font=dict(size=15, color="white"))
    return layout


def fairness_trend_chart():
    """30-day fairness and accuracy trend line chart."""
    df = get_fairness_trend_data()
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["Date"], y=df["Fairness Score"],
        name="Fairness Score",
        line=dict(color=COLORS["teal"], width=2.5, shape="spline"),
        fill="tozeroy",
        fillcolor="rgba(0,255,209,0.04)",
        mode="lines",
    ))
    fig.add_trace(go.Scatter(
        x=df["Date"], y=df["Accuracy"],
        name="Accuracy",
        line=dict(color=COLORS["blue"], width=2, shape="spline"),
        mode="lines",
    ))

    fig.update_layout(**_base_layout("Fairness & Accuracy Trends"))
    fig.update_layout(height=340)
    return fig


def bias_distribution_chart():
    """Category-level fairness vs bias risk grouped bar chart."""
    df = get_model_distribution()
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df["Category"], y=df["Fairness"],
        name="Fairness %",
        marker_color=COLORS["teal"],
        marker_line_width=0,
        opacity=0.85,
    ))
    fig.add_trace(go.Bar(
        x=df["Category"], y=df["Bias Risk"],
        name="Bias Risk %",
        marker_color=COLORS["red"],
        marker_line_width=0,
        opacity=0.85,
    ))

    fig.update_layout(**_base_layout("Fairness by Category"))
    fig.update_layout(barmode="group", height=340)
    return fig


def gauge_chart(value, title, max_val=100):
    """Gauge chart for What-If simulator results."""
    if value > 80:
        bar_color = COLORS["teal"]
    elif value > 60:
        bar_color = COLORS["yellow"]
    else:
        bar_color = COLORS["red"]

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title=dict(text=title, font=dict(color="rgba(255,255,255,0.6)", size=13)),
        number=dict(font=dict(color=bar_color, size=34)),
        gauge=dict(
            axis=dict(range=[0, max_val], tickcolor="rgba(255,255,255,0.2)", dtick=20),
            bar=dict(color=bar_color, thickness=0.7),
            bgcolor="rgba(255,255,255,0.02)",
            borderwidth=0,
            steps=[
                dict(range=[0, max_val * 0.6], color="rgba(255,80,80,0.06)"),
                dict(range=[max_val * 0.6, max_val * 0.8], color="rgba(255,215,0,0.06)"),
                dict(range=[max_val * 0.8, max_val], color="rgba(0,255,209,0.06)"),
            ],
        ),
    ))

    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="rgba(255,255,255,0.6)"),
        height=220,
        margin=dict(l=20, r=20, t=40, b=10),
    )
    return fig
