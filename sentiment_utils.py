#sentiment_utils.py

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def analyze_customer_utterance(text):
    """
    Single GROQ API call that returns:
    - sentiment: positive, neutral, negative
    - intent: main intent of the customer
    - summary: 1 sentence summary of what the customer wants
    - suggestion: actionable advice for the salesperson
    """
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""
    You are an AI sales assistant. A customer just said: "{text}"
    
    Perform the following tasks:
    1. Detect sentiment (positive, neutral, negative)
    2. Detect the main intent of the customer
    3. Summarize in ONE sentence what the customer wants
    4. Suggest a practical, real-time action the salesperson should say next

    Respond ONLY in this JSON format:
    {{
        "sentiment": "<positive/neutral/negative>",
        "intent": "<main intent>",
        "summary": "<1 sentence summary of customer need>",
        "suggestion": "<short, clear action for salesperson>"
    }}
    """

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": "You are an AI sales assistant providing actionable advice."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        raw_output = result["choices"][0]["message"]["content"].strip()

        # Parse JSON safely
        parsed = json.loads(raw_output)
        return {
            "sentiment": parsed.get("sentiment", "neutral"),
            "intent": parsed.get("intent", "unknown"),
            "summary": parsed.get("summary", "No summary provided"),
            "suggestion": parsed.get("suggestion", "Listen carefully and respond appropriately.")
        }

    except Exception as e:
        print(f"Error analyzing customer utterance: {e}")
        return {
            "sentiment": "neutral",
            "intent": "unknown",
            "summary": "No summary provided",
            "suggestion": "Listen carefully and respond appropriately."
        }
