from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.routers import health
from app.routers import channels
from app.routers import documents

# Import models to register them with SQLAlchemy
from app.models import user, conversation, document
from app.database import create_tables

# Import vector service
from app.services import vector_service

app = FastAPI(title="Store Assistant", version="0.1.0")

# FIXED CORS CONFIGURATION - ALLOW VUE.JS PORT
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000", 
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",  # Common Vue port
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables and initialize services on startup
@app.on_event("startup")
async def startup_event():
    print("🗄️ Creating database tables...")
    create_tables()
    print("✅ Database setup complete!")
    print(f"🔗 Database: {settings.DATABASE_URL}")
    print(f"⚡ Redis: {settings.REDIS_URL}")
    
    # Initialize vector service
    print("🧠 Initializing Pinecone vector service...")
    try:
        await vector_service.initialize()
        print("✅ Vector service initialized successfully!")
    except Exception as e:
        print(f"❌ Vector service initialization failed: {str(e)}")
        print("⚠️ App will continue but RAG features may not work")

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(channels.router, prefix="/channels")
app.include_router(documents.router, prefix="/documents", tags=["documents"])
app.mount("/", StaticFiles(directory="app/static", html=True), name="static")