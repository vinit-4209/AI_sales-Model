# sentiment.py
import json
import os
import requests
from dotenv import load_dotenv

from runtime_config import get_candidate_groq_models, get_groq_api_key

load_dotenv()


def _get_groq_api_key():
    api_key = get_groq_api_key()
    if not api_key:
        raise ValueError("GROQ_API_KEY is not configured.")
    return api_key


def _call_groq_chat(messages, temperature=0.7, max_tokens=1000):
    """
    Call Groq completions API with automatic multi-model fallback.
    """
    models = get_candidate_groq_models()
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {_get_groq_api_key()}",
        "Content-Type": "application/json"
    }

    last_error = None
    for model in models:
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=20)
            if response.status_code == 404 or "model_not_found" in response.text:
                continue
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
        except Exception as e:
            last_error = e
            if "model_not_found" in str(e) or "404" in str(e) or "does not exist" in str(e):
                continue
            else:
                break

    raise RuntimeError(f"Groq API call failed across all candidate models. Last error: {last_error}")


def analyze_customer_utterance(text):
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

    messages = [
        {"role": "system", "content": "You are an AI sales assistant providing actionable advice."},
        {"role": "user", "content": prompt}
    ]

    try:
        raw_output = _call_groq_chat(messages, temperature=0.7, max_tokens=300)

        # Clean any markdown code blocks
        if "```" in raw_output:
            cleaned = raw_output.replace("```json", "").replace("```", "").strip()
        else:
            cleaned = raw_output.strip()

        start = cleaned.find('{')
        end = cleaned.rfind('}')
        if start != -1 and end != -1 and end > start:
            parsed = json.loads(cleaned[start:end+1])
        else:
            parsed = json.loads(cleaned)

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

    messages = [
        {"role": "system", "content": "You summarize sales calls into structured, actionable CRM notes."},
        {"role": "user", "content": prompt}
    ]

    try:
        raw_output = _call_groq_chat(messages, temperature=0.4, max_tokens=1000)

        # Clean any markdown code blocks
        if "```" in raw_output:
            cleaned = raw_output.replace("```json", "").replace("```", "").strip()
        else:
            cleaned = raw_output.strip()

        start = cleaned.find('{')
        end = cleaned.rfind('}')
        if start != -1 and end != -1 and end > start:
            parsed = json.loads(cleaned[start:end+1])
        else:
            parsed = json.loads(cleaned)

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
