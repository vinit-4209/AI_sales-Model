import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

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
        response.raise_for_status()
        result = response.json()
        choice = result["choices"][0]
        if "message" in choice and "content" in choice["message"]:
            raw_output = choice["message"]["content"].strip()
            try:
                if raw_output.startswith('{') and raw_output.endswith('}'):
                    parsed = json.loads(raw_output)
                    if "sentiment" in parsed:
                        return {
                            "sentiment_analysis": {
                                "sentiment": parsed["sentiment"],
                                "summary": parsed.get("summary", "No summary provided")
                            }
                        }
                else:
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
                
                if any(word in raw_output.lower() for word in ["positive", "good", "great", "excellent", "happy"]):
                    return {"sentiment_analysis": {"sentiment": "positive", "summary": "Sentiment analysis completed"}}
                elif any(word in raw_output.lower() for word in ["negative", "bad", "terrible", "awful", "sad"]):
                    return {"sentiment_analysis": {"sentiment": "negative", "summary": "Sentiment analysis completed"}}
                else:
                    return {"sentiment_analysis": {"sentiment": "neutral", "summary": "Sentiment analysis completed"}}
            except json.JSONDecodeError:
                return {"sentiment_analysis": {"sentiment": "neutral", "summary": "Sentiment analysis completed"}}
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