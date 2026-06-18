import threading

import av
import numpy as np
from streamlit_webrtc import AudioProcessorBase


def _to_float_mono(audio_frame: av.AudioFrame) -> np.ndarray:
    audio = audio_frame.to_ndarray()
    original_dtype = audio.dtype

    if audio.ndim == 2:
        audio = np.mean(audio, axis=0)
    else:
        audio = audio.reshape(-1)

    audio = audio.astype(np.float32, copy=False)

    if np.issubdtype(original_dtype, np.integer):
        max_value = np.iinfo(original_dtype).max
        if max_value:
            audio = audio / float(max_value)

    return audio.astype(np.float32, copy=False)


def _resample_audio(audio: np.ndarray, source_rate: int, target_rate: int) -> np.ndarray:
    if audio.size == 0 or source_rate <= 0 or source_rate == target_rate:
        return audio.astype(np.float32, copy=False)

    target_length = max(1, int(round(audio.size * target_rate / source_rate)))
    if target_length == audio.size:
        return audio.astype(np.float32, copy=False)

    source_positions = np.arange(audio.size, dtype=np.float32)
    target_positions = np.linspace(0.0, audio.size - 1, num=target_length, dtype=np.float32)
    return np.interp(target_positions, source_positions, audio).astype(np.float32, copy=False)


class SalesCallAudioProcessor(AudioProcessorBase):
    def __init__(
        self,
        audio_queue,
        stop_event,
        target_sample_rate=16000,
        block_duration=0.05,
    ):
        self.audio_queue = audio_queue
        self.stop_event = stop_event
        self.target_sample_rate = target_sample_rate
        self.block_size = int(target_sample_rate * block_duration)
        self._buffer = np.zeros(0, dtype=np.float32)
        self._lock = threading.Lock()

    def _enqueue_audio(self, frame: av.AudioFrame):
        source_rate = int(getattr(frame, "sample_rate", self.target_sample_rate) or self.target_sample_rate)
        audio = _to_float_mono(frame)
        audio = _resample_audio(audio, source_rate, self.target_sample_rate)

        if audio.size == 0:
            return

        with self._lock:
            if self._buffer.size:
                audio = np.concatenate([self._buffer, audio])
            if self.block_size <= 0:
                self.audio_queue.put(audio.astype(np.float32, copy=False))
                self._buffer = np.zeros(0, dtype=np.float32)
                return

            while audio.size >= self.block_size:
                block = audio[: self.block_size].astype(np.float32, copy=False)
                self.audio_queue.put(block.copy())
                audio = audio[self.block_size :]

            self._buffer = audio.astype(np.float32, copy=False)

    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        self._enqueue_audio(frame)
        return frame

    async def recv_queued(self, frames):
        for frame in frames:
            self._enqueue_audio(frame)
        return frames

    def on_ended(self):
        with self._lock:
            if self._buffer.size:
                self.audio_queue.put(self._buffer.copy())
                self._buffer = np.zeros(0, dtype=np.float32)
        self.stop_event.set()
        self.audio_queue.put(None)


def build_audio_processor_factory(audio_queue, stop_event, target_sample_rate=16000, block_duration=0.05):
    def factory():
        return SalesCallAudioProcessor(
            audio_queue=audio_queue,
            stop_event=stop_event,
            target_sample_rate=target_sample_rate,
            block_duration=block_duration,
        )

    return factory
