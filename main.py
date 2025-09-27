import os
import queue
import threading
import numpy as np
import json
import signal
import sys
from datetime import datetime

from sheet import get_sheet, save_post_call_summary, extract_customer_name
from audio import start_recorder, SilenceDetector
from whisper_model import load_whisper_model, transcribe_audio
from sentiment import analyze_customer_utterance, analyze_post_call_summary


# ------------------- Config -------------------
call_transcript = []

sample_rate = 16000
block_duration = 0.05
channels = 1
frames_per_block = int(sample_rate * block_duration)

silence_detector = SilenceDetector(
    block_duration=block_duration,
    target_silence_sec=1.2,
    buffer_blocks=20,
    multiplier=1.5
)

audio_queue = queue.Queue()
audio_buffer = []
stop_event = threading.Event()

model = load_whisper_model(
    model_size="tiny.en",
    device="cpu",
    compute_type="int8"
)

LIVE_FILE = "transcript_live.txt"
STATUS_FILE = "status_live.json"
STOP_FILE = "stop_signal.txt"


# ------------------- File Utilities -------------------
def write_live(text):
    with open(LIVE_FILE, "a", encoding="utf-8") as f:
        f.write(text + "\n")


def clear_live():
    for file in [LIVE_FILE, STATUS_FILE, STOP_FILE]:
        if os.path.exists(file):
            os.remove(file)


def update_status(sentiment, summary, suggestion):
    """
    Updates live JSON file with sentiment, summary, and recommendation.
    """
    status = {
        "sentiment": sentiment,
        "summary": summary,
        "suggestion": suggestion
    }
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(status, f)


def handle_exit(signum, frame):
    print(f"\nReceived signal {signum}, stopping gracefully...")
    stop_event.set()


# ------------------- Transcription Loop -------------------
def transcriber():
    global audio_buffer, call_transcript
    silence_blocks = 0
    is_speaking = False

    try:
        print("Listening for your voice...")

        while not stop_event.is_set() and not os.path.exists(STOP_FILE):
            block = audio_queue.get()
            audio_buffer.append(block)

            if silence_detector.is_silent(block):
                if is_speaking:
                    silence_blocks += 1
                else:
                    silence_blocks = 0
            else:
                if not is_speaking:
                    print("Speech detected, recording...")
                    is_speaking = True
                silence_blocks = 0

            # Process buffer when enough silence detected
            if is_speaking and silence_blocks >= silence_detector.silence_blocks_required:
                if audio_buffer:
                    audio_data = np.concatenate(audio_buffer).flatten().astype(np.float32)

                    if np.any(audio_data):
                        texts = transcribe_audio(model, audio_data)
                        full_transcript = " ".join([t.strip() for t in texts if t.strip()])
                        full_transcript = " ".join(full_transcript.split())

                        if full_transcript:
                            timestamp = datetime.now().isoformat()
                            analysis = analyze_customer_utterance(full_transcript)

                            sentiment = analysis["sentiment"]
                            summary = analysis["summary"]
                            suggestion = analysis["suggestion"]

                            call_transcript.append(full_transcript)

                            write_live(f"[{timestamp}] {full_transcript}")
                            write_live(f"→Recommendation: {suggestion}")
                            write_live("=" * 50)

                            update_status(sentiment, summary, suggestion)

                            print("\n" + "=" * 70)
                            print(f"Timestamp        : {timestamp}")
                            print("TRANSCRIPTION & AI RECOMMENDATION")
                            print("=" * 70)
                            print(f"Customer Said    : {full_transcript}")
                            print(f"Sentiment        : {sentiment}")
                            print(f"Summary          : {summary}")
                            print(f"Recommendation   : {suggestion}")
                            print("=" * 70 + "\n")

                audio_buffer = []
                silence_blocks = 0
                is_speaking = False
                print("Listening for your voice...")

    except KeyboardInterrupt:
        stop_event.set()
        print("Stopped manually")

    finally:
        # ------------------- Save Post-Call Summary -------------------
        if call_transcript:
            final_text = " ".join(call_transcript)
            final_analysis = analyze_post_call_summary(final_text)

            overall_sentiment = final_analysis.get("sentiment", "neutral")
            overall_summary = final_analysis.get("summary", "No summary available")

            # Save JSON (preserve old keys + include new structure)
            post_summary_data = {
                "transcript": final_text,
                "sentiment": overall_sentiment,
                "summary": overall_summary,
                "structured": final_analysis
            }
            with open("post_summary.json", "w", encoding="utf-8") as f:
                json.dump(post_summary_data, f, indent=2)

            print("Post-call summary saved to post_summary.json")

            # Save to Google Sheet
            try:
                sheet = get_sheet()
                customer_name = extract_customer_name(final_text)

                save_post_call_summary(
                    sheet,
                    customer_name,
                    final_text,
                    overall_sentiment,
                    overall_summary
                )

                print("Post-call summary saved to Google Sheet")

            except Exception as e:
                print(f"Could not save to Google Sheet: {e}")

        # ------------------- Cleanup -------------------
        print("Stopping recorder and clearing buffers...")
        audio_buffer.clear()
        call_transcript.clear()
        with audio_queue.mutex:
            audio_queue.queue.clear()

        sys.exit(0)


# ------------------- Main -------------------
if __name__ == "__main__":
    clear_live()
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    recorder_thread = start_recorder(
        audio_queue,
        sample_rate,
        channels,
        frames_per_block,
        stop_event
    )

    transcriber()
