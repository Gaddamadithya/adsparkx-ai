import json
import re
from src import config

def check_escalation_triggers(
    user_query: str, 
    persona_data: dict, 
    context_chunks: list, 
    chat_history: list,
    override_threshold: float = None,
    override_max_frustration: int = None
) -> dict:
    """
    Evaluates whether the support conversation should be escalated to a human agent.
    Checks:
    1. Retrieval confidence score against threshold.
    2. Presence of billing/legal/account-sensitive keywords.
    3. Repeated user frustration/anger across turns.
    4. Absence of database content matching the user's issue.
    """
    threshold = override_threshold if override_threshold is not None else config.RETRIEVAL_CONFIDENCE_THRESHOLD
    max_frustration = override_max_frustration if override_max_frustration is not None else config.MAX_CONSECUTIVE_FRUSTRATION
    
    user_lower = user_query.lower()
    best_score = max([chunk["score"] for chunk in context_chunks]) if context_chunks else 0.0
    
    escalated = False
    reason = ""
    
    # Trigger 1: Sensitive Keywords (Billing, Security, Legal)
    matched_sensitive = []
    for word in config.SENSITIVE_KEYWORDS:
        pattern = rf"\b{re.escape(word)}\b"
        if re.search(pattern, user_lower):
            matched_sensitive.append(word)
            
    if matched_sensitive:
        escalated = True
        reason = f"Sensitive content detected (matched keywords: {', '.join(matched_sensitive)})."
        
    # Trigger 2: Low Retrieval Confidence or empty index
    elif len(context_chunks) == 0:
        escalated = True
        reason = "No relevant knowledge base documents found matching this query."
    elif best_score < threshold:
        escalated = True
        reason = f"Retrieval confidence score ({best_score:.4f}) is below the threshold ({threshold:.2f})."
        
    # Trigger 3: Repeated Frustration
    else:
        # Check current message sentiment
        current_sentiment = persona_data.get("sentiment", "Neutral")
        
        # Count consecutive frustration/anger in history
        # History format expected: list of dicts: [{"role": "user", "text": "...", "sentiment": "..."}, ...]
        consecutive_frustration = 0
        if current_sentiment in ["Frustrated", "Angry"]:
            consecutive_frustration = 1
            # Look backwards in user messages
            user_messages = [msg for msg in chat_history if msg.get("role") == "user"]
            for msg in reversed(user_messages):
                if msg.get("sentiment") in ["Frustrated", "Angry"]:
                    consecutive_frustration += 1
                else:
                    break
            
        if consecutive_frustration >= max_frustration:
            escalated = True
            reason = f"Repeated user frustration detected ({consecutive_frustration} consecutive turns of negative sentiment)."

    # If escalated, generate the Human Handoff Summary
    handoff_json = None
    if escalated:
        handoff_json = generate_handoff_summary(
            user_query=user_query,
            persona_data=persona_data,
            context_chunks=context_chunks,
            chat_history=chat_history,
            reason=reason
        )
        
    return {
        "escalated": escalated,
        "reason": reason,
        "handoff_summary": handoff_json
    }

def generate_handoff_summary(
    user_query: str, 
    persona_data: dict, 
    context_chunks: list, 
    chat_history: list,
    reason: str
) -> dict:
    """Compiles detailed, structured JSON handoff data for a human support ticket."""
    
    # Document sources list
    documents_used = list(set([chunk["source"] for chunk in context_chunks])) if context_chunks else []
    best_score = max([chunk["score"] for chunk in context_chunks]) if context_chunks else 0.0
    
    # Parse last 5 turns of conversation history for the agent
    history_summary = []
    for msg in chat_history[-5:]:
        history_summary.append({
            "role": msg.get("role"),
            "message": msg.get("text", "")[:100] + "..." if len(msg.get("text", "")) > 100 else msg.get("text", ""),
            "persona_detected": msg.get("persona", "N/A")
        })
        
    # Infer attempted actions and recommendations based on query keywords
    user_lower = user_query.lower()
    attempted_steps = []
    recommended_action = "Review customer request and contact via email/phone."
    
    if "password" in user_lower:
        attempted_steps = ["Checked password policy", "Analyzed password reset guidelines"]
        recommended_action = "Investigate if account is actively locked or if MFA codes require synchronization."
    elif "api" in user_lower or "token" in user_lower or "unauthorized" in user_lower:
        attempted_steps = ["Diagnosed request authorization header", "Checked error documentation"]
        recommended_action = "Verify API key status in database. Contact developer regarding token renewal."
    elif "billing" in user_lower or "charge" in user_lower or "refund" in user_lower:
        attempted_steps = ["Identified billing/refund request"]
        recommended_action = "Locate subscription transaction ID in Stripe, evaluate refund eligibility, and process credit manually."
    elif "domain" in user_lower or "cname" in user_lower:
        attempted_steps = ["Reviewed domain propagation times"]
        recommended_action = "Inspect portal CAA DNS records. Trigger manual SSL regeneration on portal proxy."

    handoff_data = {
        "persona": persona_data.get("persona", "Unknown"),
        "sentiment": persona_data.get("sentiment", "Neutral"),
        "user_issue_summary": user_query[:150] + "..." if len(user_query) > 150 else user_query,
        "escalation_reason": reason,
        "confidence_score": best_score,
        "documents_used": documents_used,
        "attempted_steps": attempted_steps,
        "recommended_action": recommended_action,
        "conversation_history": history_summary
    }
    
    return handoff_data
