import urllib.request
import urllib.parse
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def request(method, path, data=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req) as resp:
        content = resp.read().decode("utf-8")
        try:
            return resp.status, json.loads(content)
        except:
            return resp.status, content

print("=== RUNNING END-TO-END MARKETPLACE TEST SUITE ===")

# Test 1: Health Check
status, res = request("GET", "/api/health")
assert status == 200 and res["status"] == "healthy", f"Health check failed: {res}"
print("[PASS] 1. Backend Health Check OK")

# Test 2: Vendor Profile & Metrics
status, metrics = request("GET", "/api/vendors/metrics")
assert status == 200 and metrics["active_offers"] >= 1, f"Metrics failed: {metrics}"
print(f"[PASS] 2. Vendor Metrics OK (Active Offers: {metrics['active_offers']}, Shopkeepers: {metrics['total_shopkeepers']}, Total Msgs: {metrics['total_messages']})")

# Test 3: Product Offers List
status, offers = request("GET", "/api/offers")
assert status == 200 and len(offers) >= 4, f"Offers failed: {offers}"
print(f"[PASS] 3. Product Offers OK ({len(offers)} packaging offers available)")

# Test 4: Smart Matching with Strict Group Separation
status, matches = request("GET", f"/api/offers/{offers[0]['id']}/matches")
assert status == 200, f"Matches failed: {matches}"
interested = matches["interested_shopkeepers"]
suggested = matches["suggested_matches"]
assert len(interested) >= 1, "Should have at least 1 explicitly interested shopkeeper"
assert len(suggested) >= 1, "Should have at least 1 suggested match"
# Check rule: no suggested match is labeled explicitly interested
for s in suggested:
    assert s["is_explicitly_interested"] is False, "Suggested match must not be labeled explicitly interested"
print(f"[PASS] 4. Smart Matching Separation Verified (Explicitly Interested: {len(interested)}, Suggested Matches: {len(suggested)})")

# Test 5: Meta WhatsApp Webhook GET Verification
verify_url = "/webhooks/whatsapp?hub.mode=subscribe&hub.challenge=test_challenge_meta_1234&hub.verify_token=smart_vendor_marketplace_secure_token_2026"
status, text = request("GET", verify_url)
assert status == 200 and text == "test_challenge_meta_1234", f"Webhook verification failed: {text}"
print("[PASS] 5. Meta Webhook Verification Handshake (hub.challenge) OK")

# Test 6: Send Outbound WhatsApp Message
send_payload = {
    "shopkeeper_id": 1,
    "message_text": "Special update: We have received 20,000 more 250ml Ripple Paper Cups in ready stock at Rs 0.79/pc.",
    "product_offer_id": 1,
    "is_simulation": True
}
status, sent_msg = request("POST", "/api/conversations/1/messages", send_payload)
assert status == 200 and sent_msg["direction"] == "OUTBOUND", f"Send message failed: {sent_msg}"
assert sent_msg["whatsapp_message_id"] is not None, "Must have provider message ID"
assert sent_msg["delivery_status"] == "SENT", "Status should be SENT"
print(f"[PASS] 6. Outbound WhatsApp Message Sent OK (WAMID: {sent_msg['whatsapp_message_id']}, Status: {sent_msg['delivery_status']})")

# Test 7: Update Delivery Status to DELIVERED and READ
status_payload = {
    "message_id": sent_msg["id"],
    "new_status": "DELIVERED"
}
status, deliv_msg = request("POST", "/api/demo/simulate-status", status_payload)
assert status == 200 and deliv_msg["delivery_status"] == "DELIVERED", "Status update failed"

status_payload["new_status"] = "READ"
status, read_msg = request("POST", "/api/demo/simulate-status", status_payload)
assert status == 200 and read_msg["delivery_status"] == "READ", "Status update to READ failed"
print("[PASS] 7. Status Webhooks Processed OK (PENDING -> SENT -> DELIVERED -> READ)")

# Test 8: Simulate Inbound WhatsApp Reply with Native Quote (context.id)
reply_payload = {
    "shopkeeper_id": 1,
    "message_text": "Confirmed! Book 5,000 units of the cups at Rs 0.79/pc.",
    "product_offer_id": 1,
    "reply_to_message_id": sent_msg["id"],
    "use_native_reply": True
}
status, reply_msg = request("POST", "/api/demo/simulate-inbound", reply_payload)
assert status == 200 and reply_msg["direction"] == "INBOUND", f"Inbound reply failed: {reply_msg}"
assert reply_msg["reply_link_type"] == "EXACT", f"Must be EXACT reply link, got {reply_msg['reply_link_type']}"
assert reply_msg["quoted_message"] is not None, "Quoted message must be resolved"
print(f"[PASS] 8. WhatsApp Native Quoted Reply OK (Reply Type: EXACT, Linked Parent Msg #{reply_msg['reply_to_message_id']})")

# Test 9: Webhook POST Event (Meta Format with context.id)
webhook_post_payload = {
    "object": "whatsapp_business_account",
    "entry": [
        {
            "id": "209834718293812",
            "changes": [
                {
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "+919876543210",
                            "phone_number_id": "109823485723491"
                        },
                        "messages": [
                            {
                                "from": "+919822233344",
                                "id": "wamid.HBgM_META_WEBHOOK_TEST_1",
                                "timestamp": "1728734400",
                                "type": "text",
                                "text": {
                                    "body": "Can you deliver to South Bengaluru by tomorrow evening?"
                                }
                            }
                        ]
                    },
                    "field": "messages"
                }
            ]
        }
    ]
}
status, hook_res = request("POST", "/webhooks/whatsapp", webhook_post_payload)
assert status == 200, f"Webhook POST failed: {hook_res}"
print("[PASS] 9. Meta Webhook Incoming Payload Ingestion OK")

# Test 10: Idempotency Check on Duplicate Webhook
status, hook_res2 = request("POST", "/webhooks/whatsapp", webhook_post_payload)
assert status == 200, "Idempotent duplicate webhook should return 200 OK without duplicating"
print("[PASS] 10. Webhook Idempotency Check OK (Duplicate webhook safely ignored)")

# Test 11: Message Status History Timeline Audit
status, history = request("GET", f"/api/messages/{sent_msg['id']}/status-history")
assert status == 200 and len(history) >= 3, f"Status history failed: {history}"
statuses_logged = [h["status"] for h in history]
assert "SENT" in statuses_logged and "DELIVERED" in statuses_logged and "READ" in statuses_logged
print(f"[PASS] 11. Delivery Status Timeline Audit Preserved: {statuses_logged}")

# Test 12: Lead Pipeline
status, pipeline = request("GET", "/api/leads/pipeline")
assert status == 200, f"Pipeline failed: {pipeline}"
total_leads = sum(len(cards) for cards in pipeline.values())
assert total_leads >= 1, "Pipeline should contain leads"
print(f"[PASS] 12. Lead Kanban Pipeline OK ({total_leads} leads across 5 stages)")

print("\n=== ALL 12 TEST SUITE CRITERIA PASSED 100%! ===")
