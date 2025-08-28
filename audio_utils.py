#handles audio recording, silence detection, and related utilities.

import sounddevice as sd
import numpy as np
import queue
import threading

def is_silent(block, threshold):
    return np.sqrt(np.mean(block**2)) < threshold

def audio_callback(audio_queue):
    def callback(indata, frames, time, status):
        if status:
            print(status)
        audio_queue.put(indata.copy())
    return callback

def start_recorder(audio_queue, sample_rate, channels, frames_per_block, stop_event):
    def recorder():
        with sd.InputStream(
            samplerate=sample_rate,
            channels=channels,
            callback=audio_callback(audio_queue),
            blocksize=frames_per_block
        ):
            print("Listening... Speak now (Ctrl+C to stop)")
            while not stop_event.is_set():
                sd.sleep(100)
    thread = threading.Thread(target=recorder)
    thread.start()
    return thread