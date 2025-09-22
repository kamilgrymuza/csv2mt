from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import users, health, test
from .database import engine, Base
from .config import settings

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Micro-SaaS API",
    description="A FastAPI backend for Micro-SaaS MVP",
    version="1.0.0"
)

# Configure CORS
# Configure CORS with Railway environment variables
import os

allowed_origins = ["http://localhost:3000", "http://localhost:5173"]  # Local development

# Add Railway domains if available
if railway_domain := os.getenv("RAILWAY_PUBLIC_DOMAIN"):
    allowed_origins.append(f"https://{railway_domain}")
if railway_static := os.getenv("RAILWAY_STATIC_URL"):
    allowed_origins.append(railway_static)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(users.router)
app.include_router(test.router)


@app.get("/")
async def root():
    return {"message": "Welcome to Micro-SaaS API", "environment": settings.environment}