"""
AI Workforce Platform - Backend Entry Point

This is the main entry point for the FastAPI backend server.
Run with: python -m backend.main
Or: uvicorn backend.main:app --reload
"""
import uvicorn
from backend.src.api.main import app
from backend.src.core.config import API_HOST, API_PORT


def main():
    """Start the API server."""
    print(f"""
    ╔════════════════════════════════════════════════════════╗
    ║         AI Workforce Platform - Backend API            ║
    ╠════════════════════════════════════════════════════════╣
    ║  Server: http://{API_HOST}:{API_PORT}                          ║
    ║  Docs:   http://{API_HOST}:{API_PORT}/docs                     ║
    ╚════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        "backend.src.api.main:app",
        host=API_HOST,
        port=API_PORT,
        reload=True
    )


if __name__ == "__main__":
    main()
