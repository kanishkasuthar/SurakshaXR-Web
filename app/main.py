"""Main FastAPI Application Entrypoint for Suraksha-XR."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
from app.routers import auth, training, events, workers, admin, certificates


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize database tables and seed records on startup."""
    print(f"[Startup] Initializing {settings.PROJECT_NAME} v{settings.VERSION}...")
    init_db()
    print("[Startup] Database initialized and verified.")
    yield
    print("[Shutdown] Shutting down application cleanly.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Central Backend, Scoring Engine, AI Safety Coach, and Synchronization Hub for Suraksha-XR.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Wildcard origins cannot be combined with credentials. Keep CORS open for demo clients.
_cors_origins = settings.cors_origins_list
_allow_credentials = "*" not in _cors_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(training.router)
app.include_router(events.router)
app.include_router(workers.router)
app.include_router(admin.router)
app.include_router(certificates.router)


@app.get("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"])
def health_check():
    """Health check endpoint for container probes, mobile clients, and web monitors."""
    return {
        "status": "ok",
        "service": "Suraksha-XR Backend",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }


@app.get("/", include_in_schema=False)
def root_view():
    dash_file = _TEMPLATES_DIR / "dashboard.html"
    if dash_file.exists():
        return FileResponse(dash_file)
    return root_api_info()

@app.get("/api/info", tags=["Root"])
def root_api_info():
    """Root info page redirecting to interactive Swagger documentation."""
    return {
        "message": "Suraksha-XR Central API Service",
        "documentation": "/docs",
        "health": "/health",
        "modules": "/api/training/modules"
    }


# ========================================================
# Fullstack Web Portal & Dashboard Gateway Integration
# ========================================================
from fastapi.responses import HTMLResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from sqlalchemy.orm import Session
from fastapi import Depends
from app.database import get_db
import io

_ROOT_DIR = Path(__file__).resolve().parent.parent
_TEMPLATES_DIR = _ROOT_DIR / "templates"
_STATIC_DIR = _ROOT_DIR / "static"

if _STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

@app.get("/login", response_class=HTMLResponse, include_in_schema=False)
def serve_login():
    login_file = _TEMPLATES_DIR / "login.html"
    if login_file.exists():
        return FileResponse(login_file)
    return HTMLResponse("<h2>Suraksha-XR Admin Portal</h2><p>Please configure templates/login.html</p>")

@app.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
def serve_dashboard():
    dash_file = _TEMPLATES_DIR / "dashboard.html"
    if dash_file.exists():
        return FileResponse(dash_file)
    return HTMLResponse("<h2>Suraksha-XR Supervisor Dashboard</h2><p>Please configure templates/dashboard.html</p>")

@app.get("/app.js", include_in_schema=False)
def serve_app_js():
    f = _STATIC_DIR / "app.js"
    return FileResponse(f, media_type="text/javascript") if f.exists() else Response(status_code=404)

@app.get("/login.js", include_in_schema=False)
def serve_login_js():
    f = _STATIC_DIR / "login.js"
    return FileResponse(f, media_type="text/javascript") if f.exists() else Response(status_code=404)

@app.get("/styles.css", include_in_schema=False)
def serve_styles_css():
    f = _STATIC_DIR / "styles.css"
    return FileResponse(f, media_type="text/css") if f.exists() else Response(status_code=404)

@app.get("/api/backend-status", tags=["Web Gateway"])
def get_backend_status():
    return {
        "connected": True,
        "api_base": "",
        "demo_mode": False,
        "backend_info": {
            "status": "ok",
            "service": "Suraksha-XR Backend",
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT
        }
    }

@app.post("/api/login", tags=["Web Gateway"])
def web_login(request: schemas.LoginRequest, db: Session = Depends(get_db)):
    """Unified login handler for the supervisor dashboard."""
    username = request.username.strip()
    # Support default admin login
    if username == "admin" and request.password == "admin123":
        return {
            "access_token": "admin-session-token",
            "token": "admin-session-token",
            "role": "admin",
            "username": "admin"
        }
    # Check database users
    user = db.query(models.User).filter(models.User.username == username).first()
    if user and auth.verify_password(request.password, user.password_hash):
        token = auth.create_access_token({"sub": user.username, "role": user.role, "worker_id": user.worker_id})
        return {"access_token": token, "token": token, "role": user.role, "username": user.username}
    return Response(content='{"detail": "Invalid credentials"}', status_code=401, media_type="application/json")

@app.get("/qr/{token}", tags=["Web Gateway"])
def generate_qr(token: str):
    try:
        import qrcode
        img = qrcode.make(token)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return Response(content=buf.getvalue(), media_type="image/png")
    except Exception as e:
        return Response(content=f"Error generating QR: {e}", status_code=500)
