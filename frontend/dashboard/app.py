import streamlit as st
import pandas as pd
import plotly.express as px
import joblib
import os

st.set_page_config(page_title="IAQ Monitor", layout="wide")

st.title("🌬️ Indoor Air Quality Monitor")
st.markdown("Real-time air quality monitoring and health risk prediction")

# Load model if exists
model = None
model_path = os.path.join("..", "backend", "ml_model", "air_quality_model.pkl")
if os.path.exists(model_path):
    model = joblib.load(model_path)

# Load dataset if exists
data_path = os.path.join("..", "backend", "dataset", "processed", "labeled_data.csv")

if os.path.exists(data_path):
    df = pd.read_csv(data_path)

    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Temperature", f"{df['temperature'].iloc[-1]:.1f} °C")
    col2.metric("Humidity", f"{df['humidity'].iloc[-1]:.1f} %")
    col3.metric("Gas (raw)", f"{df['gas_raw'].iloc[-1]:.0f}")

    if model:
        latest = df[['temperature', 'humidity', 'gas_raw']].iloc[-1:]
        pred = model.predict(latest)[0]
        labels = {0: "✅ Safe", 1: "⚠️ Moderate", 2: "🚨 Dangerous"}
        colors = {0: "green", 1: "orange", 2: "red"}
        col4.markdown(f"### :{colors[pred]}[{labels[pred]}]")

    st.divider()

    # Charts
    st.subheader("Sensor readings over time")
    fig1 = px.line(df, x="timestamp", y="temperature", title="Temperature (°C)")
    st.plotly_chart(fig1, use_container_width=True)

    fig2 = px.line(df, x="timestamp", y="humidity", title="Humidity (%)")
    st.plotly_chart(fig2, use_container_width=True)

    fig3 = px.line(df, x="timestamp", y="gas_raw", title="Gas Level (raw)")
    st.plotly_chart(fig3, use_container_width=True)

else:
    st.warning("No data found. Run serial_logger.py first to collect data from ESP32.")
