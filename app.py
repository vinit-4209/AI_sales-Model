# app.py
import os
import sys
import time
import signal
import subprocess
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from sheet_utils import read_csv

st.set_page_config(page_title="AI Sales Call Assistant", page_icon="🎧", layout="wide")

# ----------------------- Session State -----------------------
if "proc" not in st.session_state:
    st.session_state.proc = None
if "listening" not in st.session_state:
    st.session_state.listening = False

# ----------------------- Styles -----------------------
st.markdown("""
<style>
.big-box {padding:16px;border-radius:14px;margin-bottom:10px;box-shadow:0 4px 12px rgba(0,0,0,0.08); border:1px solid #eee;}
.sentiment-positive {background:#e9fbea;}
.sentiment-neutral {background:#fff7db;}
.sentiment-negative {background:#ffe9e9;}
.suggestion-box {background:linear-gradient(135deg,#f0f7ff,#ffffff); border:1px solid #dbeafe;}
.transcript-box {background:#ffffff; border:1px solid #e5e7eb;}
h4 {margin-top:0;}
</style>
""", unsafe_allow_html=True)

st.title("🤖 Real-Time AI Sales Call Assistant")
st.caption("Enhanced Conversation Strategies with AI")

# ----------------------- Backend Process Helpers -----------------------
def start_backend():
    if st.session_state.proc is not None and st.session_state.proc.poll() is None:
        st.warning("Backend already running.")
        return

    env = os.environ.copy()

    # Launch main2.py as a subprocess
    python_exe = sys.executable  # same interpreter
    st.session_state.proc = subprocess.Popen(
        [python_exe, "main.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    )
    st.session_state.listening = True

def stop_backend():
    if st.session_state.proc is None:
        st.session_state.listening = False
        return
    try:
        if os.name == "nt":
            st.session_state.proc.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            st.session_state.proc.terminate()
        time.sleep(0.8)
        if st.session_state.proc.poll() is None:
            st.session_state.proc.kill()
    except Exception:
        pass
    finally:
        st.session_state.proc = None
        st.session_state.listening = False


# ----------------------- Live Section -----------------------
st.subheader("📝 Live Transcript")

df = read_csv()

if df.empty:
    st.markdown("<div class='big-box transcript-box'>Waiting for speech...</div>", unsafe_allow_html=True)
    latest = None
else:
    latest = df.tail(1).iloc[0]
    st.markdown(
        f"<div class='big-box transcript-box'><strong>Latest:</strong> {latest['Transcript']}</div>",
        unsafe_allow_html=True
    )

# ----------------------- Sentiment / Intent / Summary -----------------------
sentiment_label = (latest["Sentiment"] if latest is not None else "Neutral") or "Neutral"
sentiment_key = str(sentiment_label).lower()
emoji = {"positive": "🙂", "neutral": "😐", "negative": "🙁"}.get(sentiment_key, "😐")
sent_class = {
    "positive": "sentiment-positive",
    "neutral": "sentiment-neutral",
    "negative": "sentiment-negative"
}.get(sentiment_key, "sentiment-neutral")

intent_text = (latest["Intent"] if latest is not None else "Unknown") or "Unknown"
summary_text = (latest["Customer Summary"] if latest is not None else "") or ""

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"<div class='big-box {sent_class}'><h4>Sentiment {emoji}</h4><p style='margin:0'>{sentiment_label}</p></div>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<div class='big-box'><h4>Intent</h4><p style='margin:0'>{intent_text}</p></div>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<div class='big-box'><h4>Customer Summary</h4><p style='margin:0'>{summary_text}</p></div>", unsafe_allow_html=True)


# ----------------------- AI Suggestion -----------------------
suggestion_text = (latest["Suggestion"] if latest is not None else "") or "Waiting for customer input..."
st.subheader("💡 AI Suggested Action")
st.markdown(f"<div class='big-box suggestion-box'><p style='margin:0'><strong>{suggestion_text}</strong></p></div>", unsafe_allow_html=True)



# ----------------------- Call Controls (centered toggle button) -----------------------
st.subheader("🎤 Call Control")

# Center the button
col_left, col_center, col_right = st.columns([4, 2, 4])

with col_center:
    if st.session_state.listening:
        # Red button for End Call
        stop_style = """
            <style>
            div[data-testid="stButton"] button {
                background-color: #dc2626;
                color: white;
                border-radius: 8px;
                font-weight: bold;
                font-size: 16px;
                padding: 10px 20px;
            }
            div[data-testid="stButton"] button:hover {
                background-color: #b91c1c;
            }
            </style>
        """
        st.markdown(stop_style, unsafe_allow_html=True)
        if st.button("⏹ End Call", use_container_width=True):
            stop_backend()
    else:
        # Green button for Start Call
        start_style = """
            <style>
            div[data-testid="stButton"] button {
                background-color: #16a34a;
                color: white;
                border-radius: 8px;
                font-weight: bold;
                font-size: 16px;
                padding: 10px 20px;
            }
            div[data-testid="stButton"] button:hover {
                background-color: #15803d;
            }
            </style>
        """
        st.markdown(start_style, unsafe_allow_html=True)
        if st.button("▶️ Start Call", use_container_width=True):
            start_backend()



# ----------------------- Auto-refresh during a call -----------------------
if st.session_state.listening:
    st_autorefresh(interval=2000, key="auto_refresh_key")  # 2sec

# ----------------------- History / Analytics -----------------------
st.subheader("📊 Call History & Analytics")

if df.empty:
    st.info("No history yet.")
else:
    fcol1, fcol2, fcol3 = st.columns([2,2,2])
    with fcol1:
        sentiment_filter = st.multiselect("Filter by sentiment", ["positive", "neutral", "negative"], default=["positive", "neutral", "negative"])
    with fcol2:
        search = st.text_input("Search transcript / intent")
    with fcol3:
        st.download_button("Download CSV", data=df.to_csv(index=False).encode("utf-8"), file_name="call_history.csv", mime="text/csv")

    fdf = df.copy()
    fdf["Sentiment_l"] = fdf["Sentiment"].str.lower().fillna("neutral")
    fdf = fdf[fdf["Sentiment_l"].isin(sentiment_filter)]
    if search.strip():
        s = search.strip().lower()
        fdf = fdf[
            fdf["Transcript"].str.lower().str.contains(s, na=False) |
            fdf["Intent"].str.lower().str.contains(s, na=False) |
            fdf["Customer Summary"].str.lower().str.contains(s, na=False)
        ]

    st.dataframe(fdf.drop(columns=["Sentiment_l"]).tail(50), width="stretch")
