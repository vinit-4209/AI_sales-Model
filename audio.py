# audio.py
import sounddevice as sd
import numpy as np
import queue
import threading


class SilenceDetector:
    def __init__(self, block_duration=0.05, target_silence_sec=1.2, buffer_blocks=20, multiplier=1.5):
        self.block_duration = block_duration
        self.silence_blocks_required = int(target_silence_sec / block_duration)
        self.buffer_blocks = buffer_blocks
        self.multiplier = multiplier
        self.recent_rms = []

    def is_silent(self, block):
        rms = np.sqrt(np.mean(block**2))
        self.recent_rms.append(rms)
        if len(self.recent_rms) > self.buffer_blocks:
            self.recent_rms.pop(0)
        dynamic_threshold = max(0.01, np.mean(self.recent_rms) * self.multiplier)
        return rms < dynamic_threshold


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
        print("Recorder stopped.") 
    thread = threading.Thread(target=recorder, daemon=True)
    thread.start()
    return thread
