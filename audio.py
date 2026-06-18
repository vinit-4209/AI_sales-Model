# audio.py
import numpy as np


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
