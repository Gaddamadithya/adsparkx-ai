import os
import json
from google import genai
from google.genai import types
from src import config

def classify_customer_persona(user_message: str) -> dict:
    """
    Analyzes the user's message and classifies it into one of the three target personas:
    Technical Expert, Frustrated User, Business Executive.
    Also extracts sentiment details for dashboard analytics.
    """
    # Use key from config
    api_key = config.GEMINI_API_KEY
    if not api_key:
        # Fallback to standard default mock dictionary if no API key is configured
        return {
            "persona": "Frustrated User" if "refund" in user_message.lower() or "!" in user_message else "Technical Expert" if "api" in user_message.lower() or "token" in user_message.lower() else "Business Executive",
            "confidence": 0.9,
            "sentiment": "Frustrated" if "!" in user_message or "refund" in user_message.lower() else "Neutral",
            "reasoning": "Mock classification triggered because GEMINI_API_KEY environment variable is not configured."
        }

    client = genai.Client(api_key=api_key)

    system_instruction = (
        "You are an advanced classification engine. Your task is to analyze the "
        "sentiment, vocabulary, and tone of an incoming support message and classify "
        "it into exactly one of three customer personas:\n"
        "1. 'Technical Expert': Uses jargon, asks about APIs/code/configs/logs.\n"
        "2. 'Frustrated User': Uses emotional language, exclamation marks, or mentions urgency/inconvenience.\n"
        "3. 'Business Executive': Focuses on business impact, ROI, timelines, and brevity.\n\n"
        "Additionally, evaluate the customer's sentiment (Positive, Neutral, Frustrated, Angry).\n"
        "Provide your evaluation strictly in the requested JSON structure."
    )

    # Define structured schema output
    response_schema = {
        "type": "OBJECT",
        "properties": {
            "persona": {
                "type": "STRING",
                "enum": ["Technical Expert", "Frustrated User", "Business Executive"]
            },
            "confidence": {"type": "NUMBER"},
            "sentiment": {
                "type": "STRING",
                "enum": ["Positive", "Neutral", "Frustrated", "Angry"]
            },
            "reasoning": {"type": "STRING"}
        },
        "required": ["persona", "confidence", "sentiment", "reasoning"]
    }

    try:
        response = config.call_gemini_with_backoff(
            client.models.generate_content,
            model=config.GEMINI_MODEL,
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=response_schema,
                temperature=0.1
            )
        )
        return json.loads(response.text)
    except Exception as e:
        # Graceful fallback in case of errors
        print(f"Error in persona classification LLM call: {e}")
        # Build a rule-based backup fallback
        user_lower = user_message.lower()
        detected_persona = "Technical Expert"
        detected_sentiment = "Neutral"
        
        if any(w in user_lower for w in ["refund", "wrong", "fix", "wait", "!',", "bad", "terrible", "slow", "broken"]):
            detected_persona = "Frustrated User"
            detected_sentiment = "Frustrated"
        elif any(w in user_lower for w in ["impact", "uptime", "timeline", "sla", "resolution", "cost", "roi"]):
            detected_persona = "Business Executive"
            detected_sentiment = "Neutral"
        elif any(w in user_lower for w in ["api", "json", "token", "auth", "sdk", "header", "parameter", "error", "log"]):
            detected_persona = "Technical Expert"
            detected_sentiment = "Neutral"
            
        return {
            "persona": detected_persona,
            "confidence": 0.5,
            "sentiment": detected_sentiment,
            "reasoning": f"Rule-based classification fallback due to error: {str(e)}"
        }

# Example usage check
if __name__ == "__main__":
    test_msg = "Our production API key stopped working with a 401 Unauthorized block. Check our logs immediately."
    result = classify_customer_persona(test_msg)
    print(json.dumps(result, indent=2))
