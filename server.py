"""Suraksha-XR Person 4 Supervisor / Admin Web Command Center.

Connects directly to Person 2's FastAPI Backend as the single source of truth.
Provides real-time analytics, worker rosters, safety events, scores, and QR certificate verification.
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from pathlib import Path
import json, os, urllib.request, urllib.error, io

ROOT = Path(__file__).resolve().parent
TEMPLATES = ROOT / "templates"
STATIC = ROOT / "static"
API_BASE = os.getenv("SURAKSHA_API_BASE", "http://127.0.0.1:8000").rstrip("/")
DEMO_MODE = os.getenv("SURAKSHA_DEMO_MODE", "false").lower() == "true"


def json_response(handler, payload, status=200):
    data = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(data)


def fetch_backend(path, method="GET", body=None):
    if not API_BASE or DEMO_MODE:
        return None
    try:
        url = API_BASE + path
        data_bytes = json.dumps(body).encode("utf-8") if body else None
        headers = {"Accept": "application/json"}
        if data_bytes:
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as e:
        print(f"[Web Gateway] Backend error for {path}: {e}")
        return None


def qr_png(token):
    try:
        import qrcode
        img = qrcode.make(token)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception as e:
        print(f"[Web Gateway] QR generation error: {e}")
        return None


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        # Keep console clean
        pass

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        content_len = int(self.headers.get("Content-Length", 0))
        post_body = {}
        if content_len > 0:
            try:
                post_body = json.loads(self.rfile.read(content_len).decode("utf-8"))
            except Exception:
                pass

        if path == "/api/login":
            res = fetch_backend("/api/auth/login", method="POST", body=post_body)
            if res:
                json_response(self, res)
            else:
                # If demo mode fallback or invalid
                username = post_body.get("username", "")
                password = post_body.get("password", "")
                if username == "admin" and password == "admin123":
                    json_response(self, {"access_token": "admin-session-token", "role": "admin"})
                else:
                    json_response(self, {"detail": "Invalid credentials or backend unreachable"}, 401)
            return

        if path == "/api/events":
            res = fetch_backend("/api/v1/events", method="POST", body=post_body)
            if res:
                json_response(self, res)
            else:
                json_response(self, {"error": "Backend offline or event failed"}, 500)
            return

        self.send_error(404)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/dashboard":
            self.serve_file(TEMPLATES / "dashboard.html", "text/html; charset=utf-8")
            return
        if path == "/login":
            self.serve_file(TEMPLATES / "login.html", "text/html; charset=utf-8")
            return
        if path == "/login.js":
            self.serve_file(STATIC / "login.js", "text/javascript; charset=utf-8")
            return
        if path == "/app.js":
            self.serve_file(STATIC / "app.js", "text/javascript; charset=utf-8")
            return
        if path == "/styles.css":
            self.serve_file(STATIC / "styles.css", "text/css; charset=utf-8")
            return

        if path == "/api/backend-status":
            health = fetch_backend("/health")
            is_connected = bool(health and health.get("status") == "ok")
            json_response(self, {
                "connected": is_connected,
                "api_base": API_BASE,
                "demo_mode": DEMO_MODE,
                "backend_info": health
            })
            return

        if path == "/api/workers":
            data = fetch_backend("/api/admin/workers")
            if data is None:
                data = []
            json_response(self, data)
            return

        if path == "/api/analytics":
            data = fetch_backend("/api/admin/analytics")
            if data is None:
                data = {
                    "total_workers": 0, "workers": 0, "certified": 0,
                    "training_required": 0, "total_events": 0, "total_trainings": 0,
                    "average_score": 0.0, "total_mistakes": 0,
                    "module_scores": {"Fire": 0, "Gas": 0, "PPE": 0}
                }
            json_response(self, data)
            return

        if path == "/api/training/modules":
            data = fetch_backend("/api/training/modules")
            json_response(self, data if data is not None else [])
            return

        if path == "/api/events":
            data = fetch_backend("/api/admin/events")
            json_response(self, data if data is not None else [])
            return

        if path == "/api/results":
            data = fetch_backend("/api/admin/results")
            json_response(self, data if data is not None else [])
            return

        if path == "/api/recommendations":
            data = fetch_backend("/api/admin/recommendations")
            json_response(self, data if data is not None else [])
            return

        if path.startswith("/api/certificate/") or path.startswith("/api/certificates/"):
            worker_id = path.rsplit("/", 1)[-1]
            data = fetch_backend(f"/api/certificates/{worker_id}")
            if data is None:
                json_response(self, {"error": "Certificate not found"}, 404)
            else:
                json_response(self, data)
            return

        if path.startswith("/qr/"):
            token = path.rsplit("/", 1)[-1]
            payload = qr_png(token)
            if payload is None:
                json_response(self, {"error": "Failed to generate QR code"}, 500)
            else:
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
            return

        if path.startswith("/verify/") or path.startswith("/api/verify/"):
            token = path.rsplit("/", 1)[-1]
            data = fetch_backend(f"/api/verify/{token}")
            if data is None:
                json_response(self, {"verified": False, "message": "Certificate not found"}, 404)
            else:
                json_response(self, data)
            return

        self.send_error(404)

    def serve_file(self, path, content_type):
        if not path.exists():
            self.send_error(404)
            return
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    host = os.getenv("SURAKSHA_HOST", "127.0.0.1")
    port = int(os.getenv("SURAKSHA_PORT", "8080"))
    print(f"Suraksha-XR Web Command Center running at http://{host}:{port}")
    print(f"Connecting to FastAPI backend: {API_BASE}")
    ThreadingHTTPServer((host, port), Handler).serve_forever()
