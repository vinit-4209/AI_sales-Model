from faster_whisper import WhisperModel

model_size = "tiny.en"

# Run on GPU with FP16
model = WhisperModel(model_size, device="cpu", compute_type="int8")

# or run on GPU with INT8
# model = WhisperModel(model_size, device="cuda", compute_type="int8_float16")
# or run on CPU with INT8
# model = WhisperModel(model_size, device="cpu", compute_type="int8")

segments, _ = model.transcribe("audio_1.mp3", beam_size=5)


for segment in segments:
    print(segment.text)