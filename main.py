import queue
import threading
import numpy as np

from audio_utils import start_recorder, is_silent
from whisper_utils import load_whisper_model, transcribe_audio
from sentiment_utils import analyze_sentiment
from sheet_utils import get_sheet, append_to_sheet

sample_rate = 16000
block_duration = 0.5
chunk_duration = 5
channels = 1

SILENCE_THRESHOLD = 0.02
SILENCE_SECONDS = 15
silence_blocks_required = int(SILENCE_SECONDS / block_duration)

frames_per_chunk = int(sample_rate * chunk_duration)
frames_per_block = int(sample_rate * block_duration)

audio_queue = queue.Queue()
audio_buffer = []
stop_event = threading.Event()

model = load_whisper_model()
sheet = get_sheet()

def transcriber():
    global audio_buffer
    silence_blocks = 0
    try:
        while not stop_event.is_set():
            block = audio_queue.get()
            audio_buffer.append(block)
            if is_silent(block, SILENCE_THRESHOLD):
                silence_blocks += 1
            else:
                silence_blocks = 0
            if silence_blocks >= silence_blocks_required:
                print("Detected silence. Stopping...")
                stop_event.set()
                break
            total_frames = sum(len(b) for b in audio_buffer)
            if total_frames >= frames_per_chunk:
                audio_data = np.concatenate(audio_buffer)[:frames_per_chunk]
                audio_buffer = []
                audio_data = audio_data.flatten().astype(np.float32)
                texts = transcribe_audio(model, audio_data)
                for text in texts:
                    print(f"Transcript: {text}")
                    sentiment_result = analyze_sentiment(text)
                    if sentiment_result:
                        sentiment = sentiment_result["sentiment_analysis"]["sentiment"]
                        summary = sentiment_result["sentiment_analysis"]["summary"]
                        print(f"Sentiment: {sentiment}")
                        append_to_sheet(sheet, text, sentiment, summary)
    except KeyboardInterrupt:
        stop_event.set()
        print("Stopped manually")

if __name__ == "__main__":
    recorder_thread = start_recorder(audio_queue, sample_rate, channels, frames_per_block, stop_event)
    transcriber()