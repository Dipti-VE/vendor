import sys
from pathlib import Path
from contextlib import asynccontextmanager

# Ensure project root is in sys.path so backend.* imports work from any working directory
backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
for p in [str(project_root), str(backend_dir)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import logging

from backend.config import settings
from backend.database import engine, Base, SessionLocal
from backend.seed_data import seed_database
from backend.services.connection_manager import ws_manager

# Import routers
from backend.routers import vendors, shopkeepers, offers, conversations, messages, webhooks, demo, leads

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize tables and seed data
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db, reset=False)
    finally:
        db.close()
    logger.info("Database initialized successfully!")
    yield
    # Shutdown
    logger.info("Application shutting down...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Smart Vendor-Shopkeeper Marketplace with WhatsApp Automation, Webhook Handling, and Message Tracking",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(vendors.router, prefix=settings.API_PREFIX)
app.include_router(shopkeepers.router, prefix=settings.API_PREFIX)
app.include_router(offers.router, prefix=settings.API_PREFIX)
app.include_router(conversations.router, prefix=settings.API_PREFIX)
app.include_router(messages.router, prefix=settings.API_PREFIX)
app.include_router(leads.router, prefix=settings.API_PREFIX)
app.include_router(demo.router, prefix=settings.API_PREFIX)
app.include_router(webhooks.router) # Root level /webhooks/whatsapp

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket connection closed: {e}")
        ws_manager.disconnect(websocket)

@app.get("/")
def root():
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "demo_mode": settings.DEMO_MODE,
        "docs_url": "/docs"
    }

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "demo_mode": settings.DEMO_MODE
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
