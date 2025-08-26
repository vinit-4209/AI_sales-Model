import sounddevice as sd
import numpy as np
import queue
import threading
import sys
from faster_whisper import WhisperModel

# Google Sheets imports
import gspread
from google.oauth2.service_account import Credentials

# ------------------ Google Sheets Setup ------------------
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_file("credentials.json", scopes=scope)
client = gspread.authorize(creds)

# Open your Google Sheet (must already exist in Google Drive)
sheet = client.open("Speech_Analysis").sheet1

model_size = "tiny.en"
stop_event = threading.Event()
#Settings
sample_rate = 16000
block_duration = 0.5
chunk_duration = 2
channels = 1

SILENCE_THRESHOLD = 0.02  # Adjust as needed
SILENCE_SECONDS = 10
silence_blocks_required = int(SILENCE_SECONDS / block_duration)

frames_per_chunk = int(sample_rate * chunk_duration)
frames_per_block = int(sample_rate * block_duration)


audio_queue = queue.Queue()
audio_buffer = []

model = WhisperModel(model_size, device="cpu", compute_type="int8")

def audio_callback(indata, frames, time, status):
    if status:
        print(status)
    audio_queue.put(indata.copy())


def is_silent(block):
    return np.sqrt(np.mean(block**2)) < SILENCE_THRESHOLD


def recorder():
    with sd.InputStream(samplerate=sample_rate, channels=channels, callback=audio_callback , blocksize=frames_per_block):
        print(" Listening ... Press Ctrl+C to stop")
        while not stop_event.is_set():
            sd.sleep(100)

def transcriber():
    global audio_buffer
    silence_blocks = 0 
    try:
        while not stop_event.is_set():
            block = audio_queue.get()
            audio_buffer.append(block)
             # Check for silence
            if is_silent(block):
                silence_blocks += 1
            else:
                silence_blocks = 0

            if silence_blocks >= silence_blocks_required:
                print("Detected 10 seconds of silence. Stopping...")
                stop_event.set()
                break
            total_frames = sum(len(b) for b in audio_buffer)
            if total_frames >= frames_per_chunk:
                audio_data = np.concatenate(audio_buffer)[:frames_per_chunk]
                audio_buffer = []
                audio_data = audio_data.flatten().astype(np.float32)

                segments, _ = model.transcribe(audio_data, beam_size=1)
                for segment in segments:
                    text = segment.text.strip()
                    if text:
                        print(f"{text}")
                        # Save transcription to Google Sheet
                        sheet.append_row([text])
                        #print("Saved to Google Sheets.")
    except KeyboardInterrupt:
        stop_event.set()
        print("Stopping...")

recorder_thread = threading.Thread(target=recorder)
recorder_thread.start()
transcriber()