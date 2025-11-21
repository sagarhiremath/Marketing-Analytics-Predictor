# main.py
import streamlit as st
import pandas as pd
import time
import google.generativeai as genai
from backend import predict_campaign_revenue, to_excel 
from streamlit_lottie import st_lottie
import requests
 
# ---------------- Config ----------------
API_KEY = "AIzaSyDpCdToHWApiHB96rVBjd4lJ4r9z1_lyxA"
genai.configure(api_key=API_KEY)
st.set_page_config(page_title="Marketing Analytics Predictor", layout="wide", page_icon="📊")
 
# ---------------- Helpers & Caching ----------------
@st.cache_data
def load_lottieurl(url: str):
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None
 
ai_animation = load_lottieurl("https://assets2.lottiefiles.com/packages/lf20_touohxv0.json")
revenue_animation = load_lottieurl("https://assets9.lottiefiles.com/packages/lf20_k86wxpgr.json")
 
# ---------------- Styles ----------------
st.markdown("""
<style>
:root{--accent1:#0078D7;--accent2:#00A3FF;--glass-bg:rgba(0,30,60,0.36)}
html,body{background:linear-gradient(180deg,#041028 0%,#071937 100%);color:#e6f0fa;font-family:Poppins, sans-serif}
.glass-card{padding:1.25rem;border-radius:16px;background:var(--glass-bg);border:1.25px solid rgba(0,163,255,0.14);backdrop-filter:blur(8px);margin:0.9rem 0}
.stButton>button,.stDownloadButton>button{border-radius:12px!important;border:none!important;background:linear-gradient(90deg,var(--accent1),var(--accent2))!important;color:white!important;font-weight:700!important;padding:0.85rem 1.8rem!important;box-shadow:0 0 18px rgba(0,163,255,0.6)!important;transition:transform .18s,box-shadow .18s;cursor:pointer}
.stButton>button:hover,.stDownloadButton>button:hover{transform:translateY(-3px) scale(1.03)!important;box-shadow:0 0 34px rgba(0,163,255,1)!important}
 
/* --- MODIFIED STYLES --- */
.kpi-card{
    padding:1.6rem;
    border-radius:16px;
    background:linear-gradient(180deg,rgba(2,30,60,0.6),rgba(2,30,60,0.45));
    border:1px solid rgba(0,163,255,0.18);
    margin-bottom: 1.5rem; /* <-- ADDED SPACING */
}
.kpi-card h1{
    font-size:2.6rem;
    color:#e9fbff;
    text-shadow:0 0 20px rgba(0, 255, 127, 0.9); /* <-- CHANGED GLOW TO GREEN */
}
/* --- END OF MODIFICATIONS --- */
 
.mini-kpi{padding:0.9rem;border-radius:12px;background:rgba(255,255,255,0.02);border:1px solid rgba(0,163,255,0.08)}
.ai-card{padding:1rem;border-radius:14px;background:linear-gradient(180deg,rgba(0,70,120,0.2),rgba(0,70,120,0.08));border:1px solid rgba(0,163,255,0.12)}
.center-btn-container {display: flex; justify-content: center; margin-top: 1rem;}
.center-btn-container .stButton>button {width: 100%; max-width: 400px;}
</style>
""", unsafe_allow_html=True)
 
# ---------------- Header ----------------
st.markdown("<h1 style='text-align:center;'>🚀 Marketing Analytics Predictor</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#a9cfe8;'>✨ Enter campaign details to forecast revenue & get AI optimizations ✨</p>", unsafe_allow_html=True)
st.markdown("---")
 
if ai_animation:
    try:
        st_lottie(ai_animation, height=160, key="ai_header")
    except Exception:
        pass
 
# ---------------- Inputs Form ----------------
with st.form("campaign_input_form"):
    st.header("🎯 Campaign Input Parameters")
    col1, col2 = st.columns(2, gap="large")
    with col1:
        status = st.selectbox("Campaign Status 🚦", ["Active", "Completed"])
        channel = st.selectbox("Marketing Channel 📺", ["Facebook", "Google", "Instagram", "LinkedIn", "YouTube"])
        objective = st.selectbox("Campaign Objective 🎯", ["Awareness", "Leads", "Sales", "Traffic"])
        audience = st.selectbox("Target Audience 👥", ["Adults", "Professionals", "Seniors", "Youth"])
        geo = st.selectbox("Geographical Target 🌍", ["India", "SEA", "UK", "US"])
        creative_type = st.selectbox("Creative Type 🎨", ["Carousel", "Image", "Video"])
    with col2:
        budget = st.number_input("💰 Total Budget ($)", 100, 1_000_000, 5000, step=100, format="%d")
        spend = st.number_input("📉 Spend Till Date ($)", 0, 1_000_000, 1000, step=50, format="%d")
        impressions = st.number_input("👀 Impressions Till Date", 0, 5_000_000, 5000, step=100, format="%d")
        clicks = st.number_input("🖱️ Clicks Till Date", 0, 100_000, 100, step=10, format="%d")
        conversions = st.number_input("✅ Conversions Till Date", 0, 10_000, 10, step=1, format="%d")
        duration = st.number_input("⏳ Total Campaign Duration (days)", 1, 365, 30, format="%d")
        duration_till_date = st.number_input("📅 Duration Till Date (days)", 0, 365, 10, format="%d")
 
    # This is the styled and centered submit button for the form
    st.markdown('<div class="center-btn-container">', unsafe_allow_html=True)
    submitted = st.form_submit_button("✨ Predict Revenue & Generate Insights")
    st.markdown('</div>', unsafe_allow_html=True)
 
# ---------------- Prediction Logic (runs only after form submission) ----------------
if submitted:
    user_input = {
        "Status": status, "Channel": channel, "Objective": objective,
        "Audience": audience, "Geo": geo, "Creative_Type": creative_type,
        "Budget": float(budget), "Spend_Till_Date": float(spend),
        "Impressions_Till_Date": int(impressions), "Clicks_Till_Date": int(clicks),
        "Conversions_Till_Date": int(conversions), "Campaign_Duration": int(duration),
        "Duration_Till_Date": int(duration_till_date),
    }
 
    st.header("📈 Prediction Results & AI Analysis")
    progress_bar = st.progress(0, text="Analyzing campaign data...")
 
    # ---------- call prediction (safe) ----------
    try:
        predicted_revenue = predict_campaign_revenue(user_input)
        predicted_revenue = float(predicted_revenue)
    except Exception as e:
        st.error(f"Prediction failed: {e}")
        st.stop()
 
    # progress animation
    for p in range(0, 81, 8):
        time.sleep(0.03)
        progress_bar.progress(p, text="Forecasting revenue...")
 
    # ---------- Revenue & ROI KPI Card ----------
    # Calculate final ROI
    roi = ((predicted_revenue - budget) / budget * 100) if budget > 0 else 0
    kpi_placeholder = st.empty()
 
    # Animation loop for both Revenue and ROI
    for step in range(0, 51):
        display_rev = predicted_revenue * (step / 50)
        display_roi = roi * (step / 50)
        # Use HTML with flexbox for side-by-side layout
        kpi_html = f"""
<div class='kpi-card'>
<div style="display: flex; justify-content: space-between; align-items: start;">
<div>
<h4 style="color:#a9cfe8; margin-bottom: 0.5rem;">💵 Predicted Total Revenue</h4>
<h1 style="margin: 0;">${display_rev:,.2f}</h1>
</div>
<div style="text-align: right;">
<h4 style="color:#a9cfe8; margin-bottom: 0.5rem;">📈 Return on Investment (ROI)</h4>
<h1 style="margin: 0;">{display_roi:.1f}%</h1>
</div>
</div>
</div>
        """
        kpi_placeholder.markdown(kpi_html, unsafe_allow_html=True)
        time.sleep(0.012)
 
    # ---------- Mini KPIs ----------
    colA, colB, colC = st.columns(3)
    with colA:
        st.markdown(f"<div class='mini-kpi'><h4>💰 Total Budget</h4><p>${budget:,.0f}</p></div>", unsafe_allow_html=True)
    with colB:
        st.markdown(f"<div class='mini-kpi'><h4>📉 Spend Till Date</h4><p>${spend:,.0f}</p></div>", unsafe_allow_html=True)
    with colC:
        ctr = (clicks / impressions * 100) if impressions > 0 else 0.0
        st.markdown(f"<div class='mini-kpi'><h4>🖱️ CTR</h4><p>{ctr:.2f}%</p></div>", unsafe_allow_html=True)
 
    # ---------- AI Suggestions ----------
    progress_bar.progress(90, text="Preparing AI insights...")
    st.subheader("💡 AI Optimization Report")
    if revenue_animation:
        try:
            st_lottie(revenue_animation, height=140, key="loading_ai")
        except Exception:
            pass
 
    with st.spinner("🤖 Generating insights..."):
        try:
            model_gemini = genai.GenerativeModel("gemini")
            prompt = f"""
Campaign Data: {pd.Series(user_input).to_string()}
Predicted Final Revenue: ${predicted_revenue:,.2f}
Provide:
- Executive Summary
- 3 Actionable Suggestions
- Issues & Improvements Table
"""
            response = model_gemini.generate_content(prompt)
            ai_text = response.text
        except Exception as e:
            ai_text = f"AI suggestion unavailable: {e}"
 
        progress_bar.progress(100, text="Done!")
        st.markdown(f"<div class='ai-card'>{ai_text}</div>", unsafe_allow_html=True)
 
    # ---------- Summary + download ----------
    st.subheader("📋 Campaign Summary")
    summary_df = pd.DataFrame([user_input])
    summary_df["Predicted_Revenue"] = predicted_revenue
    summary_df["Predicted_ROI_%"] = roi
    st.dataframe(summary_df, use_container_width=True)
 
    excel_data = to_excel(summary_df)

    st.download_button("📥 Download Results", excel_data, "campaign_prediction.xlsx")

