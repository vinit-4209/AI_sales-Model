# #whisper_model.py
# from faster_whisper import WhisperModel
# import numpy as np

# def load_whisper_model(model_size="tiny.en", device="cpu", compute_type="int8"):
#     return WhisperModel(model_size, device=device, compute_type=compute_type)


# def transcribe_audio(model, audio_data, beam_size=1):
#     segments, _ = model.transcribe(audio_data, beam_size=beam_size)
#     return [segment.text.strip() for segment in segments if segment.text.strip()]


# whisper_model.py
import os
import tempfile
import numpy as np
import soundfile as sf
from groq import Groq
from dotenv import load_dotenv
load_dotenv()

# Initialize Groq client (expects GROQ_API_KEY in environment)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

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
