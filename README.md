# Suraksha-XR — Supervisor Web Command Center & Central Backend

[![Web Application CI](https://github.com/your-username/suraksha-xr-web/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/suraksha-xr-web/actions/workflows/ci.yml)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB.svg?logo=python)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

The central command dashboard and intelligent analytics engine for the **Suraksha-XR** industrial safety training platform. Built with **FastAPI**, **SQLite/SQLAlchemy**, and a responsive **Scandinavian editorial linen UI**.

---

## 🌟 Key Features

- **Supervisor Command Center:** Real-time visibility into workforce training, completion rates, safety scores, and violation analytics.
- **Interactive Training Studio:** Built-in module visualizers for Fire Safety, Gas Leak Mitigation, and PPE Hazard Inspection.
- **Worker Safety Passports:** Track individual safety records, module badges, and AI coach recommendations.
- **QR Certificate Verification:** Instant cryptographic verification of worker safety training certificates.
- **AI Safety Coach:** Evaluates training event logs in real-time to diagnose weak areas and suggest targeted remedial modules.
- **Production-Ready Unified Service:** Serves both the web interface and REST API seamlessly on a single port for zero-configuration cloud deployment.

---

## 🚀 1-Click Cloud Deployment via GitHub

### Deploy to Render (Recommended - Free Tier)
1. Fork or push this repository to your GitHub account.
2. Log into [Render.com](https://render.com/) and click **New +** → **Web Service**.
3. Select your GitHub repository.
4. Render will auto-detect the configuration via `render.yaml` / `Procfile`:
   - **Environment:** `Python`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Click **Create Web Service**. Your live URL will be active in ~1 minute!

### Deploy to Railway
1. Go to [Railway.app](https://railway.app/) and click **New Project** → **Deploy from GitHub repo**.
2. Select this repository. Railway will detect `requirements.txt` and `Procfile` and deploy automatically.

### Deploy with Docker
```bash
docker compose up --build
```
Access the application at `http://localhost:8000`.

---

## 💻 Local Quick Start

### 1. Clone & Set Up
```bash
git clone https://github.com/your-username/suraksha-xr-web.git
cd suraksha-xr-web

# Create virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Application
```bash
python run.py
```
Or with uvicorn:
```bash
uvicorn app.main:app --reload --port 8000
```

### 3. Open in Browser
- **Supervisor Web Portal:** [http://127.0.0.1:8000/login](http://127.0.0.1:8000/login)
- **Interactive API Docs (Swagger):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Documentation:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 🔐 Default Supervisor Credentials
- **Username:** `admin`
- **Password:** `admin123`

---

## 📁 Repository Structure

```text
├── app/                  # Central FastAPI Application
│   ├── main.py           # Application entrypoint & Web routes
│   ├── models.py         # SQLAlchemy ORM models
│   ├── database.py       # SQLite engine & session
│   ├── scoring.py        # Safety evaluation engine
│   ├── ai_coach.py       # AI recommendation engine
│   ├── auth.py           # JWT & password hashing
│   └── routers/          # API route handlers
├── templates/            # HTML5 UI templates
│   ├── dashboard.html    # Supervisor Command Center
│   └── login.html        # Secure Admin Login Portal
├── static/               # Assets & Client Logic
│   ├── app.js            # Dashboard interactivity & simulator
│   ├── login.js          # Authentication & theme toggler
│   └── styles.css        # Editorial Linen styling
├── tests/                # Automated pytest suite
├── Procfile              # Heroku / Render / Railway command
├── render.yaml           # Render deployment blueprint
├── Dockerfile            # Container build recipe
├── docker-compose.yml    # Docker Compose definition
├── requirements.txt      # Python dependencies
├── suraksha_xr.db        # Pre-seeded database
└── README.md             # Project documentation
```

---

## 📄 License
This project is open-source under the MIT License.
