import json
import os
import queue
import threading
from datetime import datetime

import numpy as np

from audio import SilenceDetector
from sentiment import analyze_customer_utterance, analyze_post_call_summary
from sheet import extract_customer_name, get_sheet, save_post_call_summary
from whisper_model import load_whisper_model, transcribe_audio


LIVE_FILE = "transcript_live.txt"
STATUS_FILE = "status_live.json"
STOP_FILE = "stop_signal.txt"
POST_SUMMARY_FILE = "post_summary.json"


def write_live(text):
    with open(LIVE_FILE, "a", encoding="utf-8") as file_handle:
        file_handle.write(text + "\n")


def clear_live():
    for file_name in [LIVE_FILE, STATUS_FILE, STOP_FILE]:
        if os.path.exists(file_name):
            os.remove(file_name)


def update_status(sentiment, summary, suggestion):
    status = {
        "sentiment": sentiment,
        "summary": summary,
        "suggestion": suggestion,
    }
    with open(STATUS_FILE, "w", encoding="utf-8") as file_handle:
        json.dump(status, file_handle)


class SalesCallPipeline:
    def __init__(
        self,
        model_name="whisper-large-v3-turbo",
        sample_rate=16000,
        block_duration=0.05,
        target_silence_sec=1.2,
        buffer_blocks=20,
        multiplier=1.5,
    ):
        self.model_name = model_name
        self.sample_rate = sample_rate
        self.block_duration = block_duration
        self.frames_per_block = int(sample_rate * block_duration)
        self.silence_detector = SilenceDetector(
            block_duration=block_duration,
            target_silence_sec=target_silence_sec,
            buffer_blocks=buffer_blocks,
            multiplier=multiplier,
        )
        self.audio_queue = queue.Queue()
        self.audio_buffer = []
        self.call_transcript = []
        self.stop_event = threading.Event()
        self.finalized_event = threading.Event()
        self._model = None
        self._thread = None
        self._lock = threading.Lock()

    def _ensure_model(self):
        if self._model is None:
            self._model = load_whisper_model(self.model_name)
        return self._model

    def is_running(self):
        return self._thread is not None and self._thread.is_alive()

    def start(self):
        with self._lock:
            if self.is_running():
                return

            clear_live()
            self.audio_buffer.clear()
            self.call_transcript.clear()
            self.stop_event.clear()
            self.finalized_event.clear()

            self._thread = threading.Thread(target=self._transcriber_loop, daemon=True)
            self._thread.start()

    def stop(self, wait_for_finalize=True, timeout=30):
        self.stop_event.set()
        self.audio_queue.put(None)
        if wait_for_finalize:
            self.finalized_event.wait(timeout=timeout)

    def enqueue_audio(self, audio_block):
        if not self.stop_event.is_set():
            self.audio_queue.put(audio_block)

    def _process_audio_buffer(self):
        if not self.audio_buffer:
            return

        audio_data = np.concatenate(self.audio_buffer).flatten().astype(np.float32)
        if not np.any(audio_data):
            self.audio_buffer = []
            return

        model = self._ensure_model()
        texts = transcribe_audio(model, audio_data)
        full_transcript = " ".join([text.strip() for text in texts if text.strip()])
        full_transcript = " ".join(full_transcript.split())

        if not full_transcript:
            self.audio_buffer = []
            return

        timestamp = datetime.now().isoformat()
        analysis = analyze_customer_utterance(full_transcript)

        sentiment = analysis["sentiment"]
        summary = analysis["summary"]
        suggestion = analysis["suggestion"]

        self.call_transcript.append(full_transcript)

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

        self.audio_buffer = []

    def _flush_buffer(self):
        if self.audio_buffer:
            self._process_audio_buffer()

    def _save_post_call_summary(self):
        if not self.call_transcript:
            return

        final_text = " ".join(self.call_transcript)
        final_analysis = analyze_post_call_summary(final_text)

        overall_sentiment = final_analysis.get("sentiment", "neutral")
        overall_summary = final_analysis.get("summary", "No summary available")

        post_summary_data = {
            "transcript": final_text,
            "sentiment": overall_sentiment,
            "summary": overall_summary,
            "structured": final_analysis,
        }
        with open(POST_SUMMARY_FILE, "w", encoding="utf-8") as file_handle:
            json.dump(post_summary_data, file_handle, indent=2)

        print(f"Post-call summary saved to {POST_SUMMARY_FILE}")

        try:
            sheet = get_sheet()
            customer_name = extract_customer_name(final_text)
            save_post_call_summary(
                sheet,
                customer_name,
                final_text,
                overall_sentiment,
                overall_summary,
            )
            print("Post-call summary saved to Google Sheet")
        except Exception as error:
            print(f"Could not save to Google Sheet: {error}")

    def _cleanup(self):
        self.audio_buffer.clear()
        self.call_transcript.clear()
        with self.audio_queue.mutex:
            self.audio_queue.queue.clear()

    def _finalize(self):
        try:
            self._flush_buffer()
            self._save_post_call_summary()
        finally:
            self._cleanup()
            self.finalized_event.set()

    def _transcriber_loop(self):
        silence_blocks = 0
        is_speaking = False

        try:
            print("Listening for your voice...")
            self._ensure_model()

            while not self.stop_event.is_set() or not self.audio_queue.empty():
                try:
                    block = self.audio_queue.get(timeout=0.5)
                except queue.Empty:
                    continue

                if block is None:
                    continue

                self.audio_buffer.append(block)

                if self.silence_detector.is_silent(block):
                    if is_speaking:
                        silence_blocks += 1
                else:
                    if not is_speaking:
                        print("Speech detected, recording...")
                        is_speaking = True
                    silence_blocks = 0

                if is_speaking and silence_blocks >= self.silence_detector.silence_blocks_required:
                    self._process_audio_buffer()
                    silence_blocks = 0
                    is_speaking = False
                    print("Listening for your voice...")

        except Exception as error:
            print(f"Transcription loop error: {error}")
        finally:
            self._finalize()


if __name__ == "__main__":
    print("Run this project with: streamlit run app.py")
