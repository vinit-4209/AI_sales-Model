#app.py 
import os
import sys
import time
import signal
import subprocess
import json
import streamlit as st
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="AI Sales Call Assistant", layout="wide")

# ------------------- Session State -------------------
if "proc" not in st.session_state:
    st.session_state.proc = None
if "listening" not in st.session_state:
    st.session_state.listening = False
if "post_summary" not in st.session_state:
    st.session_state.post_summary = "" 
# if "customer_name" not in st.session_state:
#     st.session_state.customer_name = ""
if "customer_phone" not in st.session_state:
    st.session_state.customer_phone = ""
# if "customer_email" not in st.session_state:
#     st.session_state.customer_email = ""
if "customer_data" not in st.session_state:
    st.session_state.customer_data = None
if "product_recommendations" not in st.session_state:
    st.session_state.product_recommendations = ""

# ------------------- Sidebar: Customer Details -------------------
st.sidebar.header("Customer Details")
#st.session_state.customer_name = st.sidebar.text_input("Customer Name", value=st.session_state.customer_name)
st.session_state.customer_phone = st.sidebar.text_input("Customer Phone", value=st.session_state.customer_phone)
#st.session_state.customer_email = st.sidebar.text_input("Customer Email", value=st.session_state.customer_email)

# Submit button for customer details
if st.sidebar.button("Fetch Customer Data", use_container_width=True):
    if st.session_state.customer_phone:
        # Import and call the CRM functions
        from crm_functions import get_client_data_from_csv, summarize_client_data
        
        # Fetch customer data from CSV
        customer_data = get_client_data_from_csv(st.session_state.customer_phone)
        st.session_state.customer_data = customer_data
        
        if customer_data:
            # Generate AI summary and recommendations
            summary = summarize_client_data(customer_data)
            st.session_state.product_recommendations = summary
            st.sidebar.success("Customer data fetched successfully!")
        else:
            st.sidebar.error("No customer found with this phone number.")
    else:
        st.sidebar.error("Please enter a phone number to fetch customer data.")

# ------------------- Styles -------------------
st.markdown("""
<style>
.big-box {padding:16px;border-radius:14px;margin-bottom:10px;box-shadow:0 4px 12px rgba(0,0,0,0.08); border:1px solid #eee;}
.sentiment-positive {background:#e9fbea;}
.sentiment-neutral {background:#fff7db;}
.sentiment-negative {background:#ffe9e9;}
.suggestion-box {background:linear-gradient(135deg,#f0f7ff,#ffffff); border:1px solid #dbeafe;}
.transcript-box {background:#ffffff; border:1px solid #e5e7eb; max-height: 300px; overflow-y: auto; white-space: pre-wrap;}
h4 {margin-top:0;}
.main-container {display: flex; gap: 20px;}
.left-column {flex: 1; min-width: 300px;}
.right-column {flex: 1; min-width: 300px;}
@media (max-width: 768px) {
    .main-container {flex-direction: column;}
}
</style>
""", unsafe_allow_html=True)

st.title("🎙 Real-Time AI Sales Call Assistant")

LIVE_FILE = "transcript_live.txt"
STATUS_FILE = "status_live.json"
STOP_FILE = "stop_signal.txt"

# ------------------- Helper Functions -------------------
def read_live():
    if os.path.exists(LIVE_FILE):
        with open(LIVE_FILE, "r", encoding="utf-8") as f:
            return f.read()
    return "Waiting for speech..."

def read_status():
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

# ------------------- Backend Control -------------------
def start_backend():
    if st.session_state.proc and st.session_state.proc.poll() is None:
        st.warning("Backend already running.")
        return
    if os.path.exists(STOP_FILE):
        os.remove(STOP_FILE)

    python_exe = sys.executable
    st.session_state.proc = subprocess.Popen(
        [python_exe, "main.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    st.session_state.listening = True
    st.session_state.post_summary = ""

def stop_backend():
    if st.session_state.proc is None:
        st.session_state.listening = False
        return

    try:
        with open(STOP_FILE, "w") as f:
            f.write("stop")
        time.sleep(3)
        if st.session_state.proc.poll() is None:
            if os.name == "nt":
                st.session_state.proc.terminate()
            else:
                st.session_state.proc.send_signal(signal.SIGTERM)
            time.sleep(1)
            if st.session_state.proc.poll() is None:
                st.session_state.proc.kill()
    except Exception as e:
        st.error(f"Error stopping backend: {e}")
    finally:
        st.session_state.proc = None
        st.session_state.listening = False
        if os.path.exists(LIVE_FILE):
            with open(LIVE_FILE, "r", encoding="utf-8") as f:
                st.session_state.post_summary = f.read()
        st.rerun()

# ------------------- Layout -------------------
left_col, right_col = st.columns([1, 1], gap="large")

# --- Left Column ---
with left_col:
    st.subheader("Call Control")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶️ Start Call", use_container_width=True):
            start_backend()
    with col2:
        if st.button("⏹ End Call", use_container_width=True):
            stop_backend()

    st.subheader("Backend Status")
    if st.session_state.proc and st.session_state.proc.poll() is None:
        st.success("Backend is running")
    else:
        st.info("Backend is stopped")

    st.subheader("Sentiment Analysis")
    status = read_status()
    sentiment_label = status.get("sentiment", "Neutral")
    sentiment_key = sentiment_label.lower()
    emoji = {"positive":"🙂", "neutral":"😐", "negative":"🙁"}.get(sentiment_key, "😐")
    sent_class = {"positive":"sentiment-positive","neutral":"sentiment-neutral","negative":"sentiment-negative"}.get(sentiment_key, "sentiment-neutral")
    summary_text = status.get("summary", "")

    st.markdown(f"<div class='big-box {sent_class}'><h4>Sentiment {emoji}</h4><p style='margin:0'>{sentiment_label}</p></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='big-box'><h4>Customer Summary</h4><p style='margin:0'>{summary_text}</p></div>", unsafe_allow_html=True)

# --- Right Column ---
with right_col:
    st.subheader("Live Transcript")
    if st.session_state.listening:
        live_text = read_live()
        st.markdown(f"<div class='big-box transcript-box'>{live_text}</div>", unsafe_allow_html=True)
    else:
        st.info("No live transcription (start a call to see it).")

    st.subheader("AI Suggestions for Customer")
    suggestion_text = status.get("suggestion", "Waiting for customer input...")
    st.markdown(f"<div class='big-box suggestion-box'><p style='margin:0'><strong>{suggestion_text}</strong></p></div>", unsafe_allow_html=True)

    # Product Recommendations Section
    if st.session_state.product_recommendations:
        st.subheader("Product Recommendations")
        st.markdown(f"<div class='big-box suggestion-box'><p style='margin:0'>{st.session_state.product_recommendations}</p></div>", unsafe_allow_html=True)

# --- Auto-refresh every 2 seconds
if st.session_state.listening:
    st_autorefresh(interval=2000, key="auto_refresh_key")

# ------------------- Post-Call Summary -------------------
st.subheader("Post-Call Summary")
col1, col2 = st.columns([3, 1])
with col2:
    if st.button("🔄 Refresh Summary"):
        st.rerun()

post_summary_file = "post_summary.json"
if os.path.exists(post_summary_file):
    try:
        with open(post_summary_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        overall_sentiment = data.get("sentiment", "Unknown")
        overall_summary = data.get("summary", "Not yet available")
        full_transcript = data.get("transcript", "")

        sent_class = {"positive":"sentiment-positive","neutral":"sentiment-neutral","negative":"sentiment-negative"}.get(overall_sentiment.lower(), "sentiment-neutral")
        emoji = {"positive":"🙂","neutral":"😐","negative":"🙁"}.get(overall_sentiment.lower(), "😐")

        st.markdown(f"<div class='big-box {sent_class}'><h4>Overall Sentiment {emoji}</h4><p>{overall_sentiment}</p></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='big-box'><h4>Overall Customer Summary</h4><p>{overall_summary}</p></div>", unsafe_allow_html=True)

        # Structured post-call sections (if available)
        structured = data.get("structured", {}) or {}
        customer_intent = structured.get("customer_intent", "")
        key_topics = structured.get("key_topics", []) or []
        objections = structured.get("objections", []) or []
        resolutions = structured.get("resolutions", []) or []
        next_steps = structured.get("next_steps", []) or []
        recommended_follow_up = structured.get("recommended_follow_up", "")
        win_risk = structured.get("win_risk", "")
        call_score = structured.get("call_score", "")

        # Consolidated Overall Call Summary box
        has_any = any([
            customer_intent, key_topics, objections, resolutions, next_steps, recommended_follow_up, win_risk, call_score != ""
        ])
        if has_any:
            topics_html = "".join([f"<li>{t}</li>" for t in key_topics]) if key_topics else ""
            obj_html = "".join([f"<li>{o}</li>" for o in objections]) if objections else ""
            res_html = "".join([f"<li>{r}</li>" for r in resolutions]) if resolutions else ""
            steps_html = "".join([f"<li>{s}</li>" for s in next_steps]) if next_steps else ""
            meta = []
           

            combined_html = "<div class='big-box'>"
            combined_html += "<h4>Overall Call Summary</h4>"
            if customer_intent:
                combined_html += f"<p style='margin:0 0 8px 0'><strong>Customer Intent:</strong> {customer_intent}</p>"
            if key_topics:
                combined_html += f"<div style='margin:8px 0'><strong>Key Topics:</strong><ul style='margin:6px 0 0 20px'>{topics_html}</ul></div>"
            if objections or resolutions:
                combined_html += "<div style='display:flex; gap:20px; flex-wrap:wrap; margin:8px 0'>"
                if objections:
                    combined_html += f"<div style='flex:1; min-width:200px'><strong>Objections</strong><ul style='margin:6px 0 0 20px'>{obj_html}</ul></div>"
                if resolutions:
                    combined_html += f"<div style='flex:1; min-width:200px'><strong>Resolutions</strong><ul style='margin:6px 0 0 20px'>{res_html}</ul></div>"
                combined_html += "</div>"
            if next_steps:
                combined_html += f"<div class='suggestion-box' style='padding:10px; margin:8px 0'><strong>Next Steps</strong><ul style='margin:6px 0 0 20px'>{steps_html}</ul></div>"
            if recommended_follow_up:
                combined_html += f"<div class='suggestion-box' style='padding:10px; margin:8px 0'><strong>Recommended Follow-up:</strong> {recommended_follow_up}</div>"
            

            st.markdown(combined_html, unsafe_allow_html=True)

        with st.expander("Full Transcript"):
            st.markdown(f"<div class='big-box transcript-box'>{full_transcript}</div>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error loading post-call summary: {e}")
else:
    st.info("No post-call summary available (will appear after ending a call).")
