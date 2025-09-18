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

def start_backend():
    if st.session_state.proc and st.session_state.proc.poll() is None:
        st.warning("Backend already running.")
        return

    # Clean up any existing stop file
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
        # Create stop file to signal backend to stop gracefully
        with open(STOP_FILE, "w") as f:
            f.write("stop")
        
        # Wait for backend to process and save files
        time.sleep(3)
        
        # Force kill if still running
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
        st.rerun()  # Use updated method

# ------------------- UI -------------------

left_col, right_col = st.columns([1, 1], gap="large")

# -LEFT COLUMN 
with left_col:
    # Call Controls
    st.subheader("Call Control")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("▶️ Start Call", use_container_width=True):
            start_backend()

    with col2:
        if st.button("⏹ End Call", use_container_width=True):
            stop_backend()

    # Backend Status 
    st.subheader("Backend Status")
    if st.session_state.proc and st.session_state.proc.poll() is None:
        st.success("Backend is running")
    else:
        st.info("Backend is stopped")
    
    # Check Google Sheets credentials
    if os.path.exists("credentials.json"):
        st.success("Google Sheets credentials found")
    else:
        st.warning("Google Sheets credentials not found - data won't be saved to sheets")

    # ----- Sentiment / Intent / Suggestion 
    st.subheader("Sentiment Analysis")
    status = read_status()
    sentiment_label = status.get("sentiment", "Neutral") or "Neutral"
    sentiment_key = sentiment_label.lower()
    emoji = {"positive":"🙂", "neutral":"😐", "negative":"🙁"}.get(sentiment_key, "😐")
    sent_class = {"positive":"sentiment-positive","neutral":"sentiment-neutral","negative":"sentiment-negative"}.get(sentiment_key, "sentiment-neutral")
    intent_text = status.get("intent", "Unknown") or "Unknown"
    summary_text = status.get("summary", "") or ""
    
    st.markdown(f"<div class='big-box {sent_class}'><h4>Sentiment {emoji}</h4><p style='margin:0'>{sentiment_label}</p></div>", unsafe_allow_html=True)
    # st.markdown(f"<div class='big-box'><h4>Intent</h4><p style='margin:0'>{intent_text}</p></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='big-box'><h4>Customer Summary</h4><p style='margin:0'>{summary_text}</p></div>", unsafe_allow_html=True)

    
# ----- RIGHT COLUMN 
with right_col:
    # ----- Live Transcript 
    st.subheader("Live Transcript")
    if st.session_state.listening:
        live_text = read_live()
        st.markdown(f"<div class='big-box transcript-box'>{live_text}</div>", unsafe_allow_html=True)
    else:
        st.info("No live transcription (start a call to see it).")

# ---- AI Suggestion
    st.subheader("AI Suggested Action")
    suggestion_text = status.get("suggestion", "Waiting for customer input...") or "Waiting for customer input..."
    st.markdown(f"<div class='big-box suggestion-box'><p style='margin:0'><strong>{suggestion_text}</strong></p></div>", unsafe_allow_html=True)

    st.markdown(f"<div class='big-box'><h4>Intent</h4><p style='margin:0'>{intent_text}</p></div>", unsafe_allow_html=True)

    


# --- Auto-refresh during call 
if st.session_state.listening:
    st_autorefresh(interval=2000, key="auto_refresh_key")  
    # refresh every 2 sec

# ---- Post-call Summary 
st.subheader("Post-Call Summary")

# Add refresh button for post-call summary
col1, col2 = st.columns([3, 1])
with col2:
    if st.button("🔄 Refresh Summary", help="Click to refresh post-call summary"):
        st.rerun()

post_summary_file = "post_summary.json"
if os.path.exists(post_summary_file):
    try:
        with open(post_summary_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        overall_sentiment = data.get("sentiment", "Unknown")
        overall_summary = data.get("summary", "Not yet summary")
        full_transcript = data.get("transcript", "")

        sent_class = {"positive":"sentiment-positive","neutral":"sentiment-neutral","negative":"sentiment-negative"}.get(overall_sentiment.lower(), "sentiment-neutral")
        emoji = {"positive":"🙂","neutral":"😐","negative":"🙁"}.get(overall_sentiment.lower(), "😐")

        st.markdown(f"<div class='big-box {sent_class}'><h4>Overall Sentiment {emoji}</h4><p>{overall_sentiment}</p></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='big-box'><h4>Overall Customer Summary</h4><p>{overall_summary}</p></div>", unsafe_allow_html=True)

        with st.expander("Full Transcript"):
            st.markdown(f"<div class='big-box transcript-box' style='white-space:pre-wrap'>{full_transcript}</div>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error loading post-call summary: {e}")
else:
    st.info("No post-call summary available (will appear after ending a call).")
