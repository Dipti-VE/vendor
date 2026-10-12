# Smart Vendor–Shopkeeper Marketplace with WhatsApp Automation and Message Tracking

A full-stack packaging supplies marketplace connecting one wholesale vendor with multiple retail shopkeepers, featuring end-to-end Meta WhatsApp Business Platform automation, webhook event capture, and 100% persistent message traceability.

---

## 🚀 Key Highlights & Architectural Overview

1. **Packaging Supplies Demonstration Domain**:
   - Pre-seeded with realistic wholesale offers: *250ml Ripple Wall Insulated Paper Cups*, *750ml Kraft Takeaway Food Containers*, *Eco-Friendly Brown Paper Bags with Handles*, and *3-Compartment Bagasse Meal Trays*.
   - 8 realistic shopkeepers (*Chai Point Express*, *Royal Biryani House*, *QuickBite Fast Food*, *Metro Sweets*, *Spice Garden*, etc.) with purchasing volume requirements, delivery locations, and target budgets.

2. **Strict Separation in Smart Matching Engine**:
   - **Group A: Explicitly Interested Shopkeepers**: Shopkeepers who explicitly submitted inquiries or requested a quote for a specific offer.
   - **Group B: Suggested Algorithmic Matches**: Shopkeepers whose product specifications, volume, budget, and delivery locations match the offer via multi-factor compatibility scoring.
   - *Rule Compliance:* No shopkeeper is ever marked as explicitly interested merely because the algorithm identified them.

3. **Core WhatsApp Messaging & 100% Persistent Traceability**:
   - Outbound and inbound messages tracked with internal ID, WhatsApp Provider ID (`wamid.HBgM...`), vendor identity, shopkeeper identity, phone numbers, product offer context, timestamps, and delivery states.
   - **Native Quoted Replies**: When a shopkeeper replies using WhatsApp's native swipe-to-reply feature, Meta's `context.id` metadata links the reply to the exact original message ID (`reply_link_type: EXACT`), rendering a quoted preview bubble.
   - **AI-Inferred Context**: Messages without native quotes can be analyzed by OpenAI (`gpt-4o-mini`) to infer relevant offer context (`reply_link_type: INFERRED`), clearly labeled with confidence and reasoning.
   - **Normal Messages**: Messages without reply references remain `reply_link_type: NONE` without false links.
   - **Delivery Status History**: Full timeline of status changes (`PENDING` → `SENT` → `DELIVERED` → `READ` → `FAILED`) preserved in `message_status_history` with provider timestamps.

4. **Official Meta WhatsApp Webhook Integration**:
   - Verification endpoint: `GET /webhooks/whatsapp` handling `hub.mode=subscribe`, `hub.challenge`, and `hub.verify_token`.
   - Ingestion endpoint: `POST /webhooks/whatsapp` processing message events, delivery statuses, idempotency deduplication, and WebSocket real-time broadcast.

5. **Demo Mode & Interactive Simulator**:
   - Fully testable independently of live WhatsApp handsets.
   - Interactive toolbar allows 1-click simulation of shopkeeper replies (with or without native quote metadata) and status progressions.
   - All simulated activity is explicitly marked (`is_demo: true`) and visually labeled.

---

## 🛠️ Technology Stack

- **Backend**: Python FastAPI 0.139, Uvicorn, SQLAlchemy 2.0 (relational SQLite / PostgreSQL compatible), Pydantic v2, HTTPX.
- **AI Engine**: OpenAI API (`gpt-4o-mini`) for context inference and smart sales pitch generation.
- **Frontend**: React 19, Vite, Vanilla CSS Design System, Lucide React icons, Canvas Confetti.
- **Real-Time Layer**: WebSockets for instant dashboard synchronization.

---

## 📂 Project Structure

```
├── backend/
│   ├── main.py                     # FastAPI entrypoint, WebSockets, Lifespan auto-seed
│   ├── config.py                   # Environment settings & Meta credentials
│   ├── database.py                 # SQLAlchemy engine & session maker
│   ├── models.py                   # Relational DB models (Vendors, Shopkeepers, Offers, Messages, etc.)
│   ├── schemas.py                  # Pydantic validation & response schemas
│   ├── seed_data.py                # Realistic packaging catalog & message seed data
│   ├── test_e2e.py                 # End-to-end automated test suite
│   ├── routers/
│   │   ├── vendors.py              # Vendor profile & analytics metrics
│   │   ├── shopkeepers.py          # Shopkeeper directory & requirements
│   │   ├── offers.py               # Product offer management & interest registration
│   │   ├── conversations.py        # WhatsApp Inbox conversations & message threads
│   │   ├── messages.py             # Complete searchable message audit trail
│   │   ├── webhooks.py             # Official Meta webhook (GET verify & POST ingest)
│   │   ├── demo.py                 # Interactive simulation endpoints
│   │   └── leads.py                # Kanban sales pipeline
│   └── services/
│       ├── whatsapp_service.py     # Meta Cloud API client & delivery tracking
│       ├── matching_service.py     # Multi-factor smart matching engine
│       ├── ai_service.py           # OpenAI context inference & reply drafting
│       └── connection_manager.py   # WebSocket broadcast manager
└── frontend/
    ├── src/
    │   ├── App.jsx                 # View router, global modals, WebSocket live toasts
    │   ├── api.js                  # Centralized fetch client & WebSocket subscriber
    │   ├── index.css               # Modern Vanilla CSS design system & WhatsApp tokens
    │   ├── components/
    │   │   ├── Navbar.jsx          # Header with status pills and actions
    │   │   ├── Sidebar.jsx         # Navigation menu & unread badges
    │   │   ├── PostOfferModal.jsx  # Modal to publish wholesale product offers
    │   │   ├── RegisterShopkeeperModal.jsx # Register shopkeepers & requirements
    │   │   ├── DeliveryStatusModal.jsx     # Status change event timeline audit
    │   │   ├── WebhookConfigModal.jsx      # Meta Webhook verification & test tools
    │   │   └── WhatsAppSimulatorDrawer.jsx # Live interactive simulator toolbar
    │   └── views/
    │       ├── OverviewDashboard.jsx   # Metrics, charts, and recent activity
    │       ├── ProductOffersView.jsx   # Offer catalog & status toggles
    │       ├── ShopkeepersView.jsx     # Retail buyer directory & requirements
    │       ├── SmartMatchingView.jsx   # Two-group matching results & WhatsApp action
    │       ├── WhatsAppInboxView.jsx   # Flagship WhatsApp Inbox with quoted replies
    │       ├── MessageHistoryView.jsx  # 100% traceable audit trail table
    │       └── LeadManagementView.jsx  # 5-stage Kanban sales pipeline
    └── vite.config.js              # Proxy configuration for /api, /webhooks, /ws
```

---

## 🏃 Quick Start Guide

### 1. Run the Backend Server
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
The backend initializes the database and seeds realistic demonstration data on startup.
- Interactive Swagger API Docs: `http://127.0.0.1:8000/docs`
- Health Endpoint: `http://127.0.0.1:8000/api/health`

### 2. Run the Frontend Dev Server
```bash
cd frontend
npm.cmd run dev -- --host 127.0.0.1 --port 5173
```
Open **`http://localhost:5173`** in your browser.

### 3. Run Automated End-to-End Tests
```bash
python backend/test_e2e.py
```
Validates all 12 acceptance criteria automatically!

---

## 📋 Acceptance Criteria Verification Matrix

| # | Acceptance Criterion | Implementation Status | Verified Evidence |
|---|----------------------|-----------------------|-------------------|
| 1 | One vendor publishes product offers at specified prices | ✅ Fully Implemented | `POST /api/offers`, `PostOfferModal` |
| 2 | Multiple shopkeepers register requirements & express interest | ✅ Fully Implemented | `POST /api/shopkeepers`, `POST /api/offers/{id}/interest` |
| 3 | Shows interested shopkeepers and potential matches separately | ✅ Fully Implemented | `SmartMatchingView` separates Group A (Explicit) from Group B (Suggested) |
| 4 | Vendor selects shopkeeper & initiates WhatsApp conversation | ✅ Fully Implemented | "Connect on WhatsApp" action initiates conversation |
| 5 | Outgoing messages stored with WAMID, vendor, shopkeeper, timestamps | ✅ Fully Implemented | `WhatsAppService.send_whatsapp_message`, `models.Message` |
| 6 | Incoming replies received through webhook and stored in DB | ✅ Fully Implemented | `POST /webhooks/whatsapp` & `demo/simulate-inbound` |
| 7 | Incoming messages mapped to correct vendor–shopkeeper conversation | ✅ Fully Implemented | Phone number matching & conversation resolution |
| 8 | Native reply metadata links response to exact original message | ✅ Fully Implemented | Provider `context.id` mapped to `reply_to_message_id` (`reply_link_type: EXACT`) |
| 9 | Messages without native reference never falsely linked | ✅ Fully Implemented | Normal messages flagged as `NONE` or `INFERRED` |
| 10 | Delivery status updates (sent, delivered, read) preserve history | ✅ Fully Implemented | `message_status_history` table & `DeliveryStatusModal` |
| 11 | Complete conversation persists across reloads/restarts | ✅ Fully Implemented | Relational SQLite database with UTC timestamps |
| 12 | Duplicate webhook events processed idempotently | ✅ Fully Implemented | Dedup check on `whatsapp_message_id` in `WhatsAppService` |
| 13 | Search & review messages by shopkeeper, offer, and date | ✅ Fully Implemented | `MessageHistoryView` with multi-factor filters & export |
| 14 | Demo mode works independently and labels simulated activity | ✅ Fully Implemented | `is_demo: true` badge on UI & interactive simulator toolbar |
