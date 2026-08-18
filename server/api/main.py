from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from server.database.connection import init_db
from server.api.auth import router as auth_router
from server.api.agents import router as agents_router
from server.api.conversations import router as conversations_router
from server.api.planning import router as planning_router
from server.api.approvals import router as approvals_router
from server.config import API_HOST, API_PORT


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup: Initialize database
    print("Initializing database...")
    init_db()
    print("Database initialized!")

    yield

    # Shutdown: cleanup if needed
    print("Shutting down...")


# Create FastAPI application
app = FastAPI(
    title="AI Workforce Platform API",
    description="REST API for managing AI agents, conversations, and automations",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Production frontend
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(agents_router, prefix="/api/v1")
app.include_router(conversations_router, prefix="/api/v1")
app.include_router(planning_router, prefix="/api/v1")
app.include_router(approvals_router, prefix="/api/v1")


@app.get("/")
def root():
    """Root endpoint - API health check."""
    return {
        "message": "AI Workforce Platform API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server.api.main:app",
        host=API_HOST,
        port=API_PORT,
        reload=True
    )
