"""
Start the FastAPI REST API server.

This runs the API on port 8001 (separate from the MCP server on port 8000).
"""
import uvicorn
from server.config import API_HOST, API_PORT

if __name__ == "__main__":
    print(f"Starting AI Workforce Platform API on {API_HOST}:{API_PORT}")
    print(f"API documentation: http://{API_HOST}:{API_PORT}/docs")
    print(f"Frontend should connect to: http://localhost:{API_PORT}")
    print("\nDefault login credentials:")
    print("  Email: admin@example.com")
    print("  Password: admin123")
    print("\nPress CTRL+C to stop the server\n")

    uvicorn.run(
        "server.api.main:app",
        host=API_HOST,
        port=API_PORT,
        reload=True,
        log_level="info"
    )
