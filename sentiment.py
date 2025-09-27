#sentiment.py
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def analyze_customer_utterance(text):
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
    3. Summarize in 1-2 sentences what the customer wants
    4. Suggest a practical, real-time action the salesperson should say next to the customer 

    Respond ONLY in this JSON format:
    {{
        "sentiment": "<positive/neutral/negative>",
        "intent": "<main intent>",
        "summary": "<1-2 sentence summary of customer need>",
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


def analyze_post_call_summary(transcript_text):
    """
    Generate a well-structured post-call summary from the entire call transcript.

    Returns a JSON-friendly dict with enhanced fields while preserving backward compatibility
    with keys: sentiment, summary.
    """
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""
    You are an expert sales call summarizer. Analyze the FULL call transcript below (customer and salesperson) and produce a concise, executive-ready summary for a CRM note.

    Important rules:
    - Focus on the CUSTOMER's needs, intents, objections, and decisions.
    - Do NOT invent details not present in the transcript.
    - Keep each field short and skimmable.

    Transcript:
    ---BEGIN TRANSCRIPT---
    {transcript_text}
    ---END TRANSCRIPT---

    Respond ONLY in this EXACT JSON object with these keys:
    {{
      "sentiment": "positive|neutral|negative",
      "summary": "2-3 sentences on customer need and outcome",
      "customer_intent": "short phrase of what customer wants",
      "key_topics": ["topic1", "topic2", "topic3"],
      "objections": ["if any, else empty"],
      "resolutions": ["how objections were handled, else empty"],
      "next_steps": ["clear next actions with owner/time if present"],
      "recommended_follow_up": "what salesperson should do next",
      "win_risk": "low|medium|high",
      "call_score": 1-10
    }}
    """

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": "You summarize sales calls into structured, actionable CRM notes."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.4
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        raw_output = result["choices"][0]["message"]["content"].strip()

        try:
            parsed = json.loads(raw_output)
        except json.JSONDecodeError:
            if "```" in raw_output:
                cleaned = raw_output.strip('`')
                start = cleaned.find('{')
                end = cleaned.rfind('}')
                if start != -1 and end != -1 and end > start:
                    parsed = json.loads(cleaned[start:end+1])
                else:
                    raise
            else:
                raise

        # Backward compatible defaults
        return {
            "sentiment": parsed.get("sentiment", "neutral"),
            "summary": parsed.get("summary", "No summary provided"),
            "customer_intent": parsed.get("customer_intent", "unknown"),
            "key_topics": parsed.get("key_topics", []),
            "objections": parsed.get("objections", []),
            "resolutions": parsed.get("resolutions", []),
            "next_steps": parsed.get("next_steps", []),
            "recommended_follow_up": parsed.get("recommended_follow_up", ""),
            "win_risk": parsed.get("win_risk", "medium"),
            "call_score": parsed.get("call_score", 7)
        }

    except Exception as e:
        print(f"Error generating post-call summary: {e}")
        return {
            "sentiment": "neutral",
            "summary": "No summary available",
            "customer_intent": "unknown",
            "key_topics": [],
            "objections": [],
            "resolutions": [],
            "next_steps": [],
            "recommended_follow_up": "",
            "win_risk": "medium",
            "call_score": 7
        }