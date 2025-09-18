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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Vite dev server
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