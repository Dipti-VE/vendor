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
    last_customer_message: Optional[str] = None,
    intent: Optional[str] = None
) -> Dict[str, str]:
    """
    Drafts a personalized, context-aware WhatsApp message for the vendor to send.
    Directly addresses previous customer message, negotiates, or confirms details.
    """
    p_name = offer_info.get("product_name", "packaging supplies")
    p_price = offer_info.get("selling_price", 1.0)
    p_qty = offer_info.get("available_quantity", 1000)
    p_moq = offer_info.get("minimum_order_quantity", 100)
    category = offer_info.get("category", "Packaging")

    # Smart fallback generator if OpenAI is unreachable
    def get_smart_fallback() -> Dict[str, str]:
        if last_customer_message:
            msg_lower = last_customer_message.lower().strip()
            # 1. Greetings
            if any(g in msg_lower for g in ["hi", "hello", "hey", "namaste", "good morning", "good evening"]):
                return {
                    "suggested_text": f"Hello {shopkeeper_name}! Great connecting with you. How can GreenPack Solutions assist {shop_name} with {p_name} or takeaway supplies today?",
                    "reasoning": "Friendly contextual greeting in response to customer hello"
                }
            # 2. Quantity inquiry / numbers
            import re
            numbers = re.findall(r'\b\d+\b', msg_lower)
            if numbers:
                req_qty = int(numbers[0])
                total_val = req_qty * p_price
                return {
                    "suggested_text": f"Great choice, {shopkeeper_name}! We have {req_qty:,} pieces of {p_name} ready in stock for you at ₹{p_price:.2f}/piece (Total ₹{total_val:,.2f}). Would you like us to dispatch to {shop_name}?",
                    "reasoning": f"Confirmed stock and pricing for customer's requested quantity ({req_qty:,} units)"
                }
            # 3. Price negotiation
            if any(w in msg_lower for g in ["rate", "price", "discount", "cheap", "cost", "kam"] for w in [g]):
                return {
                    "suggested_text": f"Hi {shopkeeper_name}, for orders exceeding {p_moq:,} units, our best wholesale rate for premium {p_name} is ₹{p_price:.2f}/unit with immediate delivery. Shall we proceed?",
                    "reasoning": "Handled wholesale price inquiry"
                }
            # 4. General inquiry response
            return {
                "suggested_text": f"Hi {shopkeeper_name}, we can certainly assist you with {p_name} for {shop_name}. Our ready stock is ₹{p_price:.2f}/unit. Would you like to confirm the delivery address?",
                "reasoning": "Contextual reply to customer inquiry"
            }

        # 5. Cold initial pitch (when no prior message)
        return {
            "suggested_text": (
                f"Hello {shopkeeper_name}! Greetings from GreenPack Solutions. "
                f"We have high quality {p_name} available at ₹{p_price:.2f}/piece (MOQ: {p_moq:,} pcs). "
                f"We currently have {p_qty:,} pieces in ready stock. Would you be interested in placing an order for {shop_name}?"
            ),
            "reasoning": "Standard packaging introductory pitch"
        }

    if not client:
        return get_smart_fallback()

    try:
        history_formatted = "\n".join(recent_history[-8:]) if recent_history else "No prior messages."
        
        prompt = f"""You are an expert sales representative for GreenPack Solutions (a B2B packaging manufacturer supplying paper cups, takeaway containers, paper bags, burger boxes) chatting directly with a shopkeeper on WhatsApp.

Shopkeeper Name: {shopkeeper_name}
Shop Name: {shop_name}
Vendor Company: GreenPack Solutions
Product Offer: {p_name} ({category})
Selling Price: ₹{p_price}/unit
Available Quantity: {p_qty:,} units
Minimum Order Quantity (MOQ): {p_moq:,} units

Recent Conversation History:
{history_formatted}

Customer's Latest Message: "{last_customer_message or 'No message yet'}"
Requested Intent: {intent or 'reply_to_customer'}

TASK:
Write the exact next WhatsApp reply message that the vendor should send to {shopkeeper_name}.
Guidelines:
1. Tone: Natural WhatsApp chat style (1-3 sentences, warm, polite, Indian business context).
2. Context Awareness: DIRECTLY answer or address what the shopkeeper said in their latest message:
   - If they asked for a quantity (e.g. "I want 600 cups"), confirm availability, mention the price per unit (₹{p_price}) or total, and ask for confirmation/delivery address.
   - If they negotiated price or asked for discount, offer a fair bulk tier or polite negotiation.
   - If they greeted ("Hi"), greet back warmly by first name and ask how you can assist their shop with {p_name} or supplies.
   - If they asked for samples, confirm sample dispatch.
   - If starting fresh, give a warm pitch.
3. NEVER use bracketed placeholders like [Your Name], [Company Name], or [Phone]. Sign off as "GreenPack Solutions" or omit signature for short chat messages.
4. Output JSON:
{{
  "suggested_text": "<exact WhatsApp message text ready to send>",
  "reasoning": "<1-sentence explanation of why this reply fits the conversation context>"
}}
"""
        response = client.chat.completions.create(
            model=settings.EXTRACTION_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.4,
            max_tokens=250
        )
        data = json.loads(response.choices[0].message.content)
        return data
    except Exception as e:
        logger.error(f"Error in generate_smart_reply_draft_ai: {e}")
        return get_smart_fallback()
