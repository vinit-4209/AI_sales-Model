import sounddevice as sd
import numpy as np
import queue
import threading
import sys
import time
from faster_whisper import WhisperModel


model_size = "tiny.en" 
stop_event = threading.Event()
sample_rate = 16000
block_duration = 0.5
chunk_duration = 2
channels = 1
silence_threshold = 0.01 
silence_timeout = 10.0  

frames_per_chunk = int(sample_rate * chunk_duration)
frames_per_block = int(sample_rate * block_duration)

audio_queue = queue.Queue()
audio_buffer = []


model = WhisperModel(
    model_size, 
    device="cpu", 
    compute_type="int8",
    cpu_threads=4,  
    num_workers=1   
)


last_speech_time = time.time()
is_speaking = False

def detect_speech(audio_data):
    """Detect if there's speech based on audio energy"""
    global is_speaking, last_speech_time
    
    
    energy = np.sqrt(np.mean(audio_data**2))
    
    if energy > silence_threshold:
        if not is_speaking:
            is_speaking = True
            print("Speech detected...")
        last_speech_time = time.time()
        return True
    else:
        if is_speaking:
            silence_duration = time.time() - last_speech_time
            if silence_duration > 5.0:  
                print(f"Silence detected... ({silence_duration:.1f}s)")
        is_speaking = False
        return False

def check_silence_timeout():
    """Check if we should stop due to prolonged silence"""
    global last_speech_time
    silence_duration = time.time() - last_speech_time
    
    if silence_duration >= silence_timeout:
        print(f"\nStopping transcription after {silence_timeout} seconds of silence")
        stop_event.set()
        return True
    return False

def audio_callback(indata, frames, time, status):
    if status:
        print(f"Audio callback status: {status}")
    audio_queue.put(indata.copy())

def recorder():
    try:
        with sd.InputStream(
            samplerate=sample_rate, 
            channels=channels, 
            callback=audio_callback, 
            blocksize=frames_per_block
        ):
            print("Listening... Press Ctrl+C to stop manually")
            print(f"Will auto-stop after {silence_timeout} seconds of silence")
            
            while not stop_event.is_set():
                sd.sleep(100)
                
                
                if check_silence_timeout():
                    break
                    
    except Exception as e:
        print(f"Error in recorder: {e}")
        stop_event.set()

def transcriber():
    global audio_buffer
    try:
        while not stop_event.is_set():
            try:
               
                block = audio_queue.get(timeout=0.1)
                audio_buffer.append(block)
                
               
                detect_speech(block.flatten().astype(np.float32))
                
                total_frames = sum(len(b) for b in audio_buffer)
                if total_frames >= frames_per_chunk:
                    audio_data = np.concatenate(audio_buffer)[:frames_per_chunk]
                    audio_buffer = []
                    audio_data = audio_data.flatten().astype(np.float32)
                    
                    # Only transcribe if speech was detected
                    if detect_speech(audio_data):
                        try:
                            segments, _ = model.transcribe(
                                audio_data, 
                                beam_size=1,
                                language="en",
                                condition_on_previous_text=False  # CPU optimization
                            )
                            for segment in segments:
                                if segment.text.strip():
                                    print(f"{segment.text}")
                        except Exception as e:
                            print(f"Transcription error: {e}")
                    
            except queue.Empty:
                continue
                
    except KeyboardInterrupt:
        print("\nManual stop requested...")
    except Exception as e:
        print(f"Error in transcriber: {e}")
    finally:
        stop_event.set()
        print("Cleaning up...")

def main():
    global last_speech_time
    
    try:
        print("Starting Real-Time Transcription")
        print(f"Model: {model_size} (CPU optimized)")
        print(f"Sample Rate: {sample_rate} Hz")
        print(f"Silence Timeout: {silence_timeout} seconds")
        print("-" * 50)
        
        
        recorder_thread = threading.Thread(target=recorder, daemon=True)
        recorder_thread.start()
        
       
        transcriber()
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        stop_event.set()
        print("Transcription stopped")
        
        
        if recorder_thread.is_alive():
            recorder_thread.join(timeout=2)
        
        print("Goodbye!")

if __name__ == "__main__":
    main()           