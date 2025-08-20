import sounddevice as sd
import numpy as np
import queue
import threading
import sys
from faster_whisper import WhisperModel

model_size = "small.en"
stop_event = threading.Event()
#Settings
sample_rate = 16000
block_duration = 0.5
chunk_duration = 2
channels = 1

frames_per_chunk = int(sample_rate * chunk_duration)
frames_per_block = int(sample_rate * block_duration)


audio_queue = queue.Queue()
audio_buffer = []

model = WhisperModel(model_size, device="cpu", compute_type="int8")

def audio_callback(indata, frames, time, status):
    if status:
        print(status)
    audio_queue.put(indata.copy())

def recorder():
    with sd.InputStream(samplerate=sample_rate, channels=channels, callback=audio_callback , blocksize=frames_per_block):
        print(" Listening ... Press Ctrl+C to stop")
        while not stop_event.is_set():
            sd.sleep(100)

def transcriber():
    global audio_buffer
    try:
        while not stop_event.is_set():
            block = audio_queue.get()
            audio_buffer.append(block)
            total_frames = sum(len(b) for b in audio_buffer)
            if total_frames >= frames_per_chunk:
                audio_data = np.concatenate(audio_buffer)[:frames_per_chunk]
                audio_buffer = []
                audio_data = audio_data.flatten().astype(np.float32)

                segments, _ = model.transcribe(audio_data, beam_size=1)
                for segment in segments:
                    print(f"{segment.text}")
    except KeyboardInterrupt:
        stop_event.set()
        print("Stopping...")

recorder_thread = threading.Thread(target=recorder)
recorder_thread.start()
transcriber()           