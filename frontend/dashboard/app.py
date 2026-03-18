import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import joblib
import os
from datetime import datetime

st.set_page_config(
    page_title="IAQ Monitor",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Dark background */
.stApp {
    background: #0f1117;
    color: #e2e8f0;
}

/* Hide default streamlit header */
#MainMenu, footer, header { visibility: hidden; }

/* Top hero banner */
.hero {
    background: linear-gradient(135deg, #1a1f2e 0%, #16213e 50%, #0f3460 100%);
    border: 1px solid #2d3748;
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.hero-title {
    font-size: 2rem;
    font-weight: 700;
    color: #ffffff;
    margin: 0;
    letter-spacing: -0.5px;
}
.hero-subtitle {
    color: #94a3b8;
    font-size: 0.95rem;
    margin-top: 0.3rem;
}
.hero-badge {
    background: #22c55e22;
    border: 1px solid #22c55e55;
    color: #22c55e;
    padding: 0.4rem 1rem;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.5px;
}
.hero-badge.warning {
    background: #f59e0b22;
    border-color: #f59e0b55;
    color: #f59e0b;
}
.hero-badge.danger {
    background: #ef444422;
    border-color: #ef444455;
    color: #ef4444;
}

/* Metric cards */
.metric-card {
    background: #1e2433;
    border: 1px solid #2d3748;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    transition: border-color 0.2s;
}
.metric-card:hover { border-color: #4a5568; }
.metric-label {
    color: #64748b;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 0.5rem;
}
.metric-value {
    font-size: 2rem;
    font-weight: 700;
    color: #f1f5f9;
    line-height: 1;
}
.metric-unit {
    font-size: 0.9rem;
    color: #94a3b8;
    font-weight: 400;
    margin-left: 4px;
}
.metric-delta {
    font-size: 0.75rem;
    margin-top: 0.4rem;
    color: #64748b;
}

/* Risk card */
.risk-safe {
    background: linear-gradient(135deg, #052e16, #14532d);
    border: 1px solid #22c55e44;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    text-align: center;
}
.risk-moderate {
    background: linear-gradient(135deg, #1c1008, #451a03);
    border: 1px solid #f59e0b44;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    text-align: center;
}
.risk-danger {
    background: linear-gradient(135deg, #1c0a0a, #450a0a);
    border: 1px solid #ef444444;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    text-align: center;
}
.risk-label {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #94a3b8;
    margin-bottom: 0.5rem;
}
.risk-value-safe   { font-size: 1.5rem; font-weight: 700; color: #22c55e; }
.risk-value-moderate { font-size: 1.5rem; font-weight: 700; color: #f59e0b; }
.risk-value-danger { font-size: 1.5rem; font-weight: 700; color: #ef4444; }

/* Section header */
.section-header {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: #4a5568;
    margin: 1.5rem 0 0.8rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #1e2433;
}

/* Warning box */
.warn-box {
    background: #1c1008;
    border: 1px solid #f59e0b44;
    border-left: 3px solid #f59e0b;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    color: #fcd34d;
    font-size: 0.9rem;
}
</style>
""", unsafe_allow_html=True)

# ── Plotly chart theme ───────────────────────────────────────────────────────
CHART_THEME = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#141824",
    font_color="#94a3b8",
    xaxis=dict(gridcolor="#1e2433", linecolor="#2d3748", tickfont=dict(size=11)),
    yaxis=dict(gridcolor="#1e2433", linecolor="#2d3748", tickfont=dict(size=11)),
    margin=dict(l=10, r=10, t=30, b=10),
)

def make_line_chart(df, col, color, label, unit):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["timestamp"], y=df[col],
        mode="lines",
        line=dict(color=color, width=2),
        fill="tozeroy",
        fillcolor=color.replace(")", ", 0.07)").replace("rgb", "rgba"),
        name=label,
        hovertemplate=f"%{{y:.1f}} {unit}<extra></extra>"
    ))
    fig.update_layout(
        height=220,
        showlegend=False,
        title=dict(text=f"{label} ({unit})", font=dict(size=13, color="#64748b"), x=0),
        **CHART_THEME
    )
    return fig

def make_gauge(value, max_val, color, title):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title=dict(text=title, font=dict(size=13, color="#64748b")),
        number=dict(font=dict(size=28, color="#f1f5f9")),
        gauge=dict(
            axis=dict(range=[0, max_val], tickcolor="#4a5568", tickfont=dict(color="#4a5568")),
            bar=dict(color=color),
            bgcolor="#1e2433",
            bordercolor="#2d3748",
            steps=[
                dict(range=[0, max_val * 0.5], color="#1a2235"),
                dict(range=[max_val * 0.5, max_val * 0.8], color="#1e2a40"),
                dict(range=[max_val * 0.8, max_val], color="#251a1a"),
            ],
        )
    ))
    fig.update_layout(height=200, paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=20, r=20, t=40, b=10))
    return fig

# ── Load data & model ────────────────────────────────────────────────────────
BASE = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(BASE, "..", "..", "backend", "ml_model", "air_quality_model.pkl")
data_path  = os.path.join(BASE, "..", "..", "backend", "dataset", "processed", "labeled_data.csv")

model = joblib.load(model_path) if os.path.exists(model_path) else None

# ── Hero banner ──────────────────────────────────────────────────────────────
now = datetime.now().strftime("%d %b %Y, %I:%M %p")

if os.path.exists(data_path):
    df = pd.read_csv(data_path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    latest = df.iloc[-1]
    temp   = latest["temperature"]
    hum    = latest["humidity"]
    gas    = latest["gas_raw"]

    risk_label = "Safe"
    badge_class = ""
    risk_class  = "risk-safe"
    risk_val_class = "risk-value-safe"

    if model:
        pred = model.predict([[temp, hum, gas]])[0]
        risk_map = {0: ("Safe", "", "risk-safe", "risk-value-safe"),
                    1: ("Moderate", "warning", "risk-moderate", "risk-value-moderate"),
                    2: ("Dangerous", "danger", "risk-danger", "risk-value-danger")}
        risk_label, badge_class, risk_class, risk_val_class = risk_map[pred]

    st.markdown(f"""
    <div class="hero">
      <div>
        <div class="hero-title">Indoor Air Quality Monitor</div>
        <div class="hero-subtitle">Last updated: {now} &nbsp;·&nbsp; {len(df)} readings collected</div>
      </div>
      <div class="hero-badge {badge_class}">● &nbsp;{risk_label}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Metric row ───────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="metric-card">
          <div class="metric-label">Temperature</div>
          <div class="metric-value">{temp:.1f}<span class="metric-unit">°C</span></div>
          <div class="metric-delta">Avg: {df['temperature'].mean():.1f} °C</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-card">
          <div class="metric-label">Humidity</div>
          <div class="metric-value">{hum:.1f}<span class="metric-unit">%</span></div>
          <div class="metric-delta">Avg: {df['humidity'].mean():.1f} %</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="metric-card">
          <div class="metric-label">Gas Level</div>
          <div class="metric-value">{int(gas)}<span class="metric-unit">raw</span></div>
          <div class="metric-delta">Avg: {df['gas_raw'].mean():.0f}</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="{risk_class}">
          <div class="risk-label">Health Risk</div>
          <div class="{risk_val_class}">{risk_label}</div>
        </div>""", unsafe_allow_html=True)

    # ── Gauges ───────────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Live Gauges</div>', unsafe_allow_html=True)
    g1, g2, g3 = st.columns(3)
    g1.plotly_chart(make_gauge(temp, 60, "#38bdf8", "Temperature °C"),  use_container_width=True)
    g2.plotly_chart(make_gauge(hum,  100, "#818cf8", "Humidity %"),      use_container_width=True)
    g3.plotly_chart(make_gauge(gas,  4095, "#fb923c", "Gas Raw"),         use_container_width=True)

    # ── Time series ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Sensor History</div>', unsafe_allow_html=True)
    st.plotly_chart(make_line_chart(df, "temperature", "rgb(56,189,248)",  "Temperature", "°C"),  use_container_width=True)
    st.plotly_chart(make_line_chart(df, "humidity",    "rgb(129,140,248)", "Humidity",    "%"),    use_container_width=True)
    st.plotly_chart(make_line_chart(df, "gas_raw",     "rgb(251,146,60)",  "Gas Level",   "raw"),  use_container_width=True)

    # ── Risk distribution ────────────────────────────────────────────────────
    if "label" in df.columns:
        st.markdown('<div class="section-header">Risk Distribution</div>', unsafe_allow_html=True)
        label_map = {0: "Safe", 1: "Moderate", 2: "Dangerous"}
        df["Risk"] = df["label"].map(label_map)
        counts = df["Risk"].value_counts().reset_index()
        counts.columns = ["Risk", "Count"]
        fig_pie = px.pie(
            counts, names="Risk", values="Count",
            color="Risk",
            color_discrete_map={"Safe": "#22c55e", "Moderate": "#f59e0b", "Dangerous": "#ef4444"},
            hole=0.55
        )
        fig_pie.update_layout(
            height=280,
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#94a3b8",
            legend=dict(bgcolor="rgba(0,0,0,0)"),
            margin=dict(l=10, r=10, t=10, b=10)
        )
        st.plotly_chart(fig_pie, use_container_width=True)

else:
    st.markdown(f"""
    <div class="hero">
      <div>
        <div class="hero-title">Indoor Air Quality Monitor</div>
        <div class="hero-subtitle">No data yet — connect your ESP32 and run serial_logger.py</div>
      </div>
      <div class="hero-badge warning">● &nbsp;Waiting</div>
    </div>
    <div class="warn-box">
      No dataset found at <code>backend/dataset/processed/labeled_data.csv</code>.<br>
      Run <strong>serial_logger.py</strong> to start collecting data from your ESP32.
    </div>
    """, unsafe_allow_html=True)