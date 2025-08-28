from faster_whisper import WhisperModel
import numpy as np

def load_whisper_model(model_size="tiny.en", device="cpu", compute_type="int8"):
    return WhisperModel(model_size, device=device, compute_type=compute_type)

def transcribe_audio(model, audio_data, beam_size=1):
    segments, _ = model.transcribe(audio_data, beam_size=beam_size)
    return [segment.text.strip() for segment in segments if segment.text.strip()]