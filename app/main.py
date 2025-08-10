from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.routers import health
from app.routers import channels

# Import models to register them with SQLAlchemy
from app.models import user, conversation, document
from app.database import create_tables

app = FastAPI(title="Store Assistant", version="0.1.0")

# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    print("🗄️ Creating database tables...")
    create_tables()
    print("✅ Database setup complete!")
    print(f"🔗 Database: {settings.DATABASE_URL}")
    print(f"⚡ Redis: {settings.REDIS_URL}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.ALLOW_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(channels.router, prefix="/channels")
app.mount("/", StaticFiles(directory="app/static", html=True), name="static")