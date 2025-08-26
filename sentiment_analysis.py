import sounddevice as sd
import numpy as np
import queue
import threading
import os
import json
from faster_whisper import WhisperModel
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests

# ----------------- Load Environment Variables -----------------
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ----------------- Google Sheets Setup -----------------

scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)


sheet = client.open("Speech_Analysis").sheet1

# ----------------- Whisper Model -----------------
model_size = "tiny.en"
model = WhisperModel(model_size, device="cpu", compute_type="int8")


sample_rate = 16000
block_duration = 0.5
chunk_duration = 5
channels = 1

SILENCE_THRESHOLD = 0.02
SILENCE_SECONDS = 15   # stop if 15s silence
silence_blocks_required = int(SILENCE_SECONDS / block_duration)

frames_per_chunk = int(sample_rate * chunk_duration)
frames_per_block = int(sample_rate * block_duration)

audio_queue = queue.Queue()
audio_buffer = []
stop_event = threading.Event()

# ----------------- Groq Sentiment Analysis -----------------
def analyze_sentiment(text):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.1-8b-instant",  
        "messages": [
            {"role": "system", "content": "You are a sentiment analysis service. Analyze the sentiment of the given text and respond with ONLY a JSON object in this exact format: {\"sentiment\": \"positive\", \"summary\": \"brief summary\"}. Use positive, negative, or neutral for sentiment."},
            {"role": "user", "content": text}
        ],
        "temperature": 0
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        result = response.json()
        choice = result["choices"][0]
        
        if "message" in choice and "content" in choice["message"]:
            raw_output = choice["message"]["content"].strip()
            
            # Try to extract JSON from the response
            try:
                # Look for JSON content in the response
                if raw_output.startswith('{') and raw_output.endswith('}'):
                    parsed = json.loads(raw_output)
                    # Ensure we have the expected structure
                    if "sentiment" in parsed:
                        return {
                            "sentiment_analysis": {
                                "sentiment": parsed["sentiment"],
                                "summary": parsed.get("summary", "No summary provided")
                            }
                        }
                else:
                    # Try to find JSON within the response
                    start_idx = raw_output.find('{')
                    end_idx = raw_output.rfind('}')
                    if start_idx != -1 and end_idx != -1:
                        json_str = raw_output[start_idx:end_idx+1]
                        parsed = json.loads(json_str)
                        if "sentiment" in parsed:
                            return {
                                "sentiment_analysis": {
                                    "sentiment": parsed["sentiment"],
                                    "summary": parsed.get("summary", "No summary provided")
                                }
                            }
                    
                    # Fallback: try to determine sentiment from text
                    if any(word in raw_output.lower() for word in ["positive", "good", "great", "excellent", "happy"]):
                        return {
                            "sentiment_analysis": {
                                "sentiment": "positive",
                                "summary": "Sentiment analysis completed"
                            }
                        }
                    elif any(word in raw_output.lower() for word in ["negative", "bad", "terrible", "awful", "sad"]):
                        return {
                            "sentiment_analysis": {
                                "sentiment": "negative",
                                "summary": "Sentiment analysis completed"
                            }
                        }
                    else:
                        return {
                            "sentiment_analysis": {
                                "sentiment": "neutral",
                                "summary": "Sentiment analysis completed"
                            }
                        }
                        
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract sentiment from text
                if any(word in raw_output.lower() for word in ["positive", "good", "great", "excellent", "happy"]):
                    return {
                        "sentiment_analysis": {
                            "sentiment": "positive",
                            "summary": "Sentiment analysis completed"
                        }
                    }
                elif any(word in raw_output.lower() for word in ["negative", "bad", "terrible", "awful", "sad"]):
                    return {
                        "sentiment_analysis": {
                            "sentiment": "negative",
                            "summary": "Sentiment analysis completed"
                        }
                    }
                else:
                    return {
                        "sentiment_analysis": {
                            "sentiment": "neutral",
                            "summary": "Sentiment analysis completed"
                        }
                    }
                    
        else:
            print("Unexpected response structure:", result)
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None
    except Exception as e:
        print(f"Error parsing sentiment: {e}")
        print("Raw response:", result if 'result' in locals() else "No response")
        return None




# ----------------- Audio Handling -----------------
def audio_callback(indata, frames, time, status):
    if status:
        print(status)
    audio_queue.put(indata.copy())

def is_silent(block):
    return np.sqrt(np.mean(block**2)) < SILENCE_THRESHOLD

def recorder():
    with sd.InputStream(samplerate=sample_rate, channels=channels, callback=audio_callback, blocksize=frames_per_block):
        print("Listening... Speak now (Ctrl+C to stop)")
        while not stop_event.is_set():
            sd.sleep(100)

def transcriber():
    global audio_buffer
    silence_blocks = 0
    try:
        while not stop_event.is_set():
            block = audio_queue.get()
            audio_buffer.append(block)

            if is_silent(block):
                silence_blocks += 1
            else:
                silence_blocks = 0

            if silence_blocks >= silence_blocks_required:
                print("Detected silence. Stopping...")
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
                        print(f"Transcript: {text}")
                        
                        sentiment_result = analyze_sentiment(text)
                        if sentiment_result:
                            sentiment = sentiment_result["sentiment_analysis"]["sentiment"]
                            summary = sentiment_result["sentiment_analysis"]["summary"]
                            print(f"Sentiment: {sentiment} ")

                            # Save to Google Sheet
                            sheet.append_row([text, sentiment, summary])
    except KeyboardInterrupt:
        stop_event.set()
        print("Stopped manually")

# ----------------- Run -----------------
recorder_thread = threading.Thread(target=recorder)
recorder_thread.start()
transcriber()
