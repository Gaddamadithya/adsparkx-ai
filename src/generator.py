import os
from google import genai
from google.genai import types
from src import config

def generate_adaptive_response(user_query: str, persona: str, context_chunks: list) -> dict:
    """
    Generates a persona-aligned response grounded in the retrieved context.
    Enforces strict context utilization rules.
    """
    # Assemble raw text context
    context_text = "\n\n".join([
        f"Source [{chunk['source']} (Page: {chunk['page']})]: {chunk['text']}" 
        for chunk in context_chunks
    ])

    # Establish the instruction rules based on persona
    if persona == "Technical Expert":
        persona_instructions = (
            "You are a Senior Systems Engineer. Provide clear root-cause analysis, "
            "configuration specifications, and precise API pathways or code blocks. "
            "Keep technical descriptions exact and structured. Include raw HTTP details, "
            "header parameters, and JSON blocks where appropriate."
        )
    elif persona == "Frustrated User":
        persona_instructions = (
            "You are a deeply empathetic, reassuring Customer Care Specialist. "
            "Begin with a warm, genuine validation of their difficulty. For example: "
            "'I understand how frustrating it is to deal with this...' or 'I realize this is "
            "causing a major interruption, and I want to help resolve it quickly.' "
            "Use straightforward, reassuring, and simple action-oriented bullet steps. "
            "Avoid confusing jargon, code blocks, and system internals."
        )
    else:  # Business Executive
        persona_instructions = (
            "You are a concise Client Relations Director. Focus on direct business outcomes, "
            "service recovery timelines, operational impacts, and cost/agreement alignment. "
            "Keep responses extremely brief, highly professional, and skip unnecessary "
            "technical configuration details."
        )

    # Core grounding system prompt
    full_system_prompt = (
        f"{persona_instructions}\n\n"
        "CRITICAL RULES:\n"
        "- Base your response ONLY on the provided FACTUAL CONTEXT DOCUMENTS below.\n"
        "- Do not hallucinate, assume, or generalize facts not found in the documents.\n"
        "- If the answer to the user's query cannot be found in the context documents, reply with: "
        "'I am sorry, but the documentation provided does not contain sufficient details to answer your query. "
        "I will check with a live representative to help you further.'\n\n"
        f"FACTUAL CONTEXT DOCUMENTS:\n{context_text}"
    )

    api_key = config.GEMINI_API_KEY
    if not api_key:
        # Fallback offline generator for testing without an API key
        if persona == "Technical Expert":
            response_text = (
                "#### Diagnostic Response (Offline Mode)\n"
                "System initialized in test/offline mode. Query matches: `Technical Expert`.\n"
                "API endpoint check required. Recommended parameter: `Authorization: Bearer <key>`. "
                "Verify connection settings."
            )
        elif persona == "Frustrated User":
            response_text = (
                "I understand how frustrating it is to encounter this issue. I am here to help you step-by-step.\n\n"
                "Here is what we can do to resolve it:\n"
                "- Verify your login email.\n"
                "- Clear your browser cache and refresh.\n\n"
                "Please let me know if these steps work!"
            )
        else:
            response_text = (
                "We appreciate your patience. Our technical team is reviewing this incident.\n\n"
                "**Estimated Resolution Time:** 15 minutes.\n"
                "**Operational Impact:** Moderate."
            )
        return {
            "response": response_text,
            "system_prompt": full_system_prompt
        }

    client = genai.Client(api_key=api_key)

    try:
        response = config.call_gemini_with_backoff(
            client.models.generate_content,
            model=config.GEMINI_MODEL,
            contents=user_query,
            config=types.GenerateContentConfig(
                system_instruction=full_system_prompt,
                temperature=0.2
            )
        )
        return {
            "response": response.text,
            "system_prompt": full_system_prompt
        }
    except Exception as e:
        print(f"Error in Gemini response generation: {e}")
        return {
            "response": f"An error occurred while generating the response: {str(e)}",
            "system_prompt": full_system_prompt
        }
