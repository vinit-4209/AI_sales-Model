import streamlit as st
import queue, threading, numpy as np
from datetime import datetime

from audio_utils import start_recorder, SilenceDetector
from whisper_utils import load_whisper_model, transcribe_audio
from sentiment_utils import analyze_customer_utterance
from sheet_utils import append_to_csv

# ------------------- Config -------------------
st.set_page_config(page_title="AI Sales Call Assistant", page_icon="🎧", layout="wide")

sample_rate = 16000
block_duration = 0.05
channels = 1
frames_per_block = int(sample_rate * block_duration)

silence_detector = SilenceDetector(block_duration=block_duration, target_silence_sec=1.2)
audio_queue = queue.Queue()
audio_buffer = []
stop_event = threading.Event()
model = load_whisper_model(model_size="tiny", device="cpu", compute_type="int8")  # lightweight model

# ------------------- CSS -------------------
st.markdown("""
    <style>
    .stButton button {
        background: linear-gradient(135deg, #3b82f6, #2563eb);
        color: white; border-radius: 8px;
        font-weight: 600; font-size: 14px;
        padding: 6px 14px; border: none;
    }
    .stButton button:hover {
        background: linear-gradient(135deg, #2563eb, #1d4ed8);
        transform: translateY(-2px);
    }
    </style>
""", unsafe_allow_html=True)

# ------------------- Session State -------------------
if "call_active" not in st.session_state:
    st.session_state.call_active = False
if "transcript" not in st.session_state:
    st.session_state.transcript = ""
if "analysis" not in st.session_state:
    st.session_state.analysis = {}

# ------------------- Toggle Call -------------------
def toggle_call():
    if not st.session_state.call_active:
        # Start new call
        st.session_state.call_active = True
        st.session_state.transcript = ""
        st.session_state.analysis = {}
        stop_event.clear()
        threading.Thread(target=transcriber, daemon=True).start()
    else:
        # End call
        st.session_state.call_active = False
        stop_event.set()

# ------------------- Transcriber -------------------
def transcriber():
    global audio_buffer
    recorder_thread = start_recorder(audio_queue, sample_rate, channels, frames_per_block, stop_event)

    silence_blocks, is_speaking = 0, False

    transcript_box = st.empty()
    analysis_box = st.empty()
    suggestion_box = st.empty()

    while not stop_event.is_set():
        try:
            block = audio_queue.get(timeout=1)  # timeout to check stop_event
        except queue.Empty:
            continue

        audio_buffer.append(block)

        if silence_detector.is_silent(block):
            if is_speaking:
                silence_blocks += 1
        else:
            is_speaking, silence_blocks = True, 0

        if is_speaking and silence_blocks >= silence_detector.silence_blocks_required:
            if audio_buffer:
                audio_data = np.concatenate(audio_buffer).flatten().astype(np.float32)
                if np.any(audio_data):
                    texts = transcribe_audio(model, audio_data)
                    transcript = " ".join([t.strip() for t in texts if t.strip()])

                    if transcript:
                        st.session_state.transcript += " " + transcript
                        analysis = analyze_customer_utterance(transcript)
                        st.session_state.analysis = analysis

                        # ---- Update UI live ----
                        transcript_box.info(st.session_state.transcript)
                        if analysis:
                            sentiment = analysis.get("sentiment", "neutral")
                            emoji = {"positive": "😊", "neutral": "😐", "negative": "😞"}.get(sentiment, "😐")
                            analysis_box.markdown(
                                f"### 📊 Smart Analysis\n\n**Sentiment:** {emoji} {sentiment.capitalize()}  \n"
                                f"**Summary:** {analysis.get('summary', '')}  \n"
                                f"**Intent:** {analysis.get('intent', '')}"
                            )
                            suggestion_box.markdown(
                                f"### 💡 AI Suggestions\n\n✅ {analysis.get('suggestion', '')}"
                            )

                        # Save to CSV
                        timestamp = datetime.now().isoformat()
                        append_to_csv(
                            timestamp,
                            transcript,
                            analysis["sentiment"],
                            analysis["summary"],
                            analysis["intent"],
                            analysis["suggestion"]
                        )

            audio_buffer, silence_blocks, is_speaking = [], 0, False

    # ---- Clean stop ----
    recorder_thread.join(timeout=2)
    with audio_queue.mutex:
        audio_queue.queue.clear()
    audio_buffer.clear()

# ------------------- UI -------------------
st.title("🤖 Real-Time AI Sales Call Assistant")

# Call Control
col1, col2 = st.columns([1, 4])
with col1:
    button_label = "▶️ Start Call" if not st.session_state.call_active else "🔴 End Call"
    st.button(button_label, on_click=toggle_call)

# Live Transcription
st.markdown("### 📝 Real-Time Transcription")
if st.session_state.transcript:
    st.info(st.session_state.transcript)
else:
    st.info("Waiting for speech...")

# Smart Analysis + AI Suggestions
if st.session_state.analysis:
    sentiment = st.session_state.analysis.get("sentiment", "neutral")
    emoji = {"positive": "😊", "neutral": "😐", "negative": "😞"}.get(sentiment, "😐")

    st.markdown("### 📊 Smart Analysis")
    st.write(f"**Sentiment:** {emoji} {sentiment.capitalize()}")
    st.write(f"**Customer Summary:** {st.session_state.analysis.get('summary', '')}")
    st.write(f"**Intent:** {st.session_state.analysis.get('intent', '')}")

    st.markdown("### 💡 AI Suggestions")
    st.success(st.session_state.analysis.get("suggestion", "Listen carefully and respond appropriately."))
