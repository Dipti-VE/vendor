import json
import logging
from typing import Optional, Dict, Any, List
from openai import OpenAI
from ..config import settings

logger = logging.getLogger(__name__)

client: Optional[OpenAI] = None
if settings.OPENAI_API_KEY:
    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
    except Exception as e:
        logger.warning(f"Could not initialize OpenAI client: {e}")

def infer_message_context_ai(
    incoming_text: str,
    active_offers: List[Dict[str, Any]],
    recent_messages: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Uses OpenAI to analyze an incoming WhatsApp reply without native quote metadata
    and determine whether it implicitly refers to a specific product offer or earlier message.
    Returns:
    {
       "inferred": bool,
       "confidence": float (0.0 to 1.0),
       "target_offer_id": int | None,
       "target_message_id": int | None,
       "reason": str
    }
    """
    if not client or not active_offers:
        return {
            "inferred": False,
            "confidence": 0.0,
            "target_offer_id": None,
            "target_message_id": None,
            "reason": "AI assistant unavailable or no active offers"
        }

    try:
        offers_summary = [
            f"Offer #{o['id']}: {o['product_name']} ({o['category']}) at ₹{o['selling_price']}/unit, stock {o['available_quantity']}"
            for o in active_offers
        ]
        history_summary = [
            f"Msg #{m['id']} [{m['direction']}]: '{m['text']}'"
            for m in recent_messages[-5:]
        ]

        prompt = f"""
You are an AI assistant in a packaging marketplace (paper cups, takeaway containers, paper bags, burger boxes).
Analyze this incoming WhatsApp message from a shopkeeper:
Incoming Message: "{incoming_text}"

Active Offers:
{chr(10).join(offers_summary)}

Recent Conversation History:
{chr(10).join(history_summary)}

Determine if the incoming message clearly discusses or negotiates a specific offer or earlier message.
Respond ONLY with a JSON object in this format:
{{
  "inferred": true/false,
  "confidence": 0.0 to 1.0,
  "target_offer_id": <int or null>,
  "target_message_id": <int or null>,
  "reason": "<short 1-sentence explanation of why this offer/message was inferred>"
}}
Only set "inferred": true if confidence is >= 0.70 and the context is clear.
"""
        response = client.chat.completions.create(
            model=settings.EXTRACTION_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.2,
            max_tokens=200
        )
        data = json.loads(response.choices[0].message.content)
        return data
    except Exception as e:
        logger.error(f"Error calling OpenAI infer_message_context: {e}")
        return {
            "inferred": False,
            "confidence": 0.0,
            "target_offer_id": None,
            "target_message_id": None,
            "reason": f"AI analysis error: {str(e)}"
        }

def generate_smart_reply_draft_ai(
    offer_info: Dict[str, Any],
    shopkeeper_name: str,
    shop_name: str,
    recent_history: List[str],
    intent: str = "initial_pitch"
) -> Dict[str, str]:
    """
    Drafts a personalized, professional WhatsApp message for the vendor to send.
    """
    if not client:
        # Fallback template generator
        p_name = offer_info.get("product_name", "packaging supplies")
        p_price = offer_info.get("selling_price", 0.0)
        p_qty = offer_info.get("available_quantity", 0)
        p_moq = offer_info.get("minimum_order_quantity", 100)
        
        fallback_text = (
            f"Hello {shopkeeper_name}! Greetings from GreenPack Solutions. "
            f"We have high quality {p_name} available at ₹{p_price:.2f}/piece (MOQ: {p_moq:,} pcs). "
            f"We currently have {p_qty:,} pieces in ready stock. Would you be interested in placing an order for {shop_name}?"
        )
        return {
            "suggested_text": fallback_text,
            "reasoning": "Standard packaging template generated"
        }

    try:
        prompt = f"""
You are an expert sales assistant for a packaging manufacturer contacting a shopkeeper on WhatsApp.
Shopkeeper Name: {shopkeeper_name}
Shop Name: {shop_name}
Product Offer: {offer_info.get('product_name')} ({offer_info.get('category')})
Selling Price: ₹{offer_info.get('selling_price')}/unit
Available Quantity: {offer_info.get('available_quantity')} units
Minimum Order Quantity (MOQ): {offer_info.get('minimum_order_quantity')} units
Intent: {intent}
Recent messages: {recent_history}

Create a warm, concise, professional WhatsApp message in polite Indian business style.
Include the product name, price in ₹, MOQ, and a courteous call to action.
Return JSON:
{{
  "suggested_text": "...",
  "reasoning": "..."
}}
"""
        response = client.chat.completions.create(
            model=settings.EXTRACTION_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=300
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"Error in generate_smart_reply_draft_ai: {e}")
        p_name = offer_info.get("product_name", "packaging supplies")
        p_price = offer_info.get("selling_price", 0.0)
        return {
            "suggested_text": f"Hello {shopkeeper_name}! We have {p_name} available at ₹{p_price:.2f} per piece. Are you interested in purchasing?",
            "reasoning": "Fallback draft due to API exception"
        }
