"""CLI Runner for Suraksha-XR FastAPI Backend."""
import os
import uvicorn

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "True").lower() == "true"

    print(f"Starting Suraksha-XR Backend on http://{host}:{port}")
    print(f"Interactive API Docs (Swagger): http://127.0.0.1:{port}/docs")
    print(f"ReDoc Documentation: http://127.0.0.1:{port}/redoc")
    uvicorn.run("app.main:app", host=host, port=port, reload=reload)
