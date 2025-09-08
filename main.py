#main2.py 

import os
import queue
import threading
import numpy as np
from datetime import datetime

from sheet_utils import append_to_csv, append_to_sheet, get_sheet
from audio_utils import start_recorder, SilenceDetector
from whisper_utils import load_whisper_model, transcribe_audio
from sentiment_utils import analyze_customer_utterance

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

model = load_whisper_model(model_size="tiny", device="cpu", compute_type="int8")
sheet = None

def transcriber():
    global audio_buffer, sheet
    silence_blocks = 0
    is_speaking = False

    try:
        print("Listening for your voice...") 

        while not stop_event.is_set():
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

            if is_speaking and silence_blocks >= silence_detector.silence_blocks_required:
                if audio_buffer:
                    audio_data = np.concatenate(audio_buffer).flatten().astype(np.float32)

                    if np.any(audio_data):
                        texts = transcribe_audio(model, audio_data)
                        full_transcript = " ".join([t.strip() for t in texts if t.strip()])
                        full_transcript = " ".join(full_transcript.split())

                        if full_transcript:
                            timestamp = datetime.now().isoformat()

                            # Sentiment + intent + summary + suggestion
                            analysis = analyze_customer_utterance(full_transcript)
                            sentiment = analysis["sentiment"]
                            intent = analysis["intent"]
                            customer_summary = analysis["summary"]
                            suggestion = analysis["suggestion"]

                          
                            append_to_csv(timestamp, full_transcript, sentiment, customer_summary, intent, suggestion)

                            
                            if sheet is None:
                                try:
                                    sheet = get_sheet()
                                except Exception as e:
                                    print(f"Google Sheet not connected: {e}")
                            if sheet is not None:
                                append_to_sheet(sheet, timestamp, full_transcript, sentiment, customer_summary, intent, suggestion)

                            
                            print("\n" + "="*70)
                            print(f"Timestamp        : {timestamp}")
                            print("TRANSCRIPTION & AI SUGGESTION")
                            print("="*70)
                            print(f"Customer Said    : {full_transcript}")
                            print(f"Sentiment        : {sentiment}")
                            print(f"Intent           : {intent}")
                            print(f"Customer Summary : {customer_summary}")
                            print(f"Suggested Action : {suggestion}")
                            print("="*70 + "\n")

                audio_buffer = []
                silence_blocks = 0
                is_speaking = False
                print("Listening for your voice...")
    except KeyboardInterrupt:
        stop_event.set()
        print("Stopped manually")


    print("Stopping recorder and clearing buffers...")
    audio_buffer.clear()
    with audio_queue.mutex:
        audio_queue.queue.clear()

if __name__ == "__main__":
    recorder_thread = start_recorder(
        audio_queue,
        sample_rate,
        channels,
        frames_per_block,
        stop_event
    )
    transcriber()
