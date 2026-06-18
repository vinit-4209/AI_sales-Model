
# whisper_model.py
import os
import tempfile
import numpy as np
import soundfile as sf
from groq import Groq
from dotenv import load_dotenv

from runtime_config import get_groq_api_key
load_dotenv()

def _get_client():
    api_key = get_groq_api_key()
    if not api_key:
        raise ValueError("GROQ_API_KEY is not configured.")
    return Groq(api_key=api_key)

def load_whisper_model(model_size="whisper-large-v3-turbo", **kwargs):
    """
    Placeholder for compatibility with existing main.py structure.
    Groq API doesn't load a model locally.
    """
    return model_size  # Return model name as a dummy handle


def transcribe_audio(model, audio_data, **kwargs):
    import tempfile, os, soundfile as sf

    # Save numpy audio to a temp WAV file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
        sf.write(tmp_wav.name, audio_data, 16000)
        tmp_wav_path = tmp_wav.name

    try:
        client = _get_client()
        with open(tmp_wav_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                file=(tmp_wav_path, audio_file.read()),
                model=model,
                temperature=0,
                response_format="verbose_json",
            )

        # ✅ Fix: access as an object, not dict
        text = getattr(transcription, "text", "").strip()
        return [text] if text else []

    except Exception as e:
        print(f"[Groq Transcription Error]: {e}")
        return []

    finally:
        if os.path.exists(tmp_wav_path):
            os.remove(tmp_wav_path)
