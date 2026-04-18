<div align="center">
  <img src="https://raw.githubusercontent.com/tandpfun/skill-icons/main/icons/Docker.svg" height="40" alt="docker logo"  />
  <img width="12" />
  <img src="https://raw.githubusercontent.com/tandpfun/skill-icons/main/icons/Python.svg" height="40" alt="python logo"  />
  <img width="12" />
  <img src="https://raw.githubusercontent.com/tandpfun/skill-icons/main/icons/FastAPI.svg" height="40" alt="fastapi logo"  />
  <img width="12" />
  <img src="https://raw.githubusercontent.com/tandpfun/skill-icons/main/icons/GCP.svg" height="40" alt="gcp logo"  />
  <img width="12" />
  <img src="https://raw.githubusercontent.com/tandpfun/skill-icons/main/icons/Vercel.svg" height="40" alt="vercel logo"  />
</div>

<br/>

<div align="center">
  <h1 align="center">🌊 OceanEye</h1>
  <p align="center">
    <strong>AI-Powered Real-Time Maritime Intelligence Platform</strong>
  </p>
  <p align="center">
    Detecting Illegal, Unreported, and Unregulated (IUU) fishing through AIS telemetry and Claude AI. 
  </p>
</div>

<br/>

## 🎯 Global Impact
OceanEye is designed for maritime authorities, coast guards, and environmental organizations protecting Exclusive Economic Zones (EEZ). By combining satellite telemetry with advanced language models, the platform acts as an autonomous intelligence analyst, identifying dark vessel operations, transshipment networks, and loitering patterns in real-time.

---

## ✨ Features
- 🧠 **Claude AI Automated Analysis:** Calculates live risk scores (0-100) and drafts tactical intelligence briefings for every tracked vessel.
- 📡 **Live AIS Tracking:** Direct WebSocket streaming from `aisstream.io` for zero-latency vessel geolocation rendering.
- 🚩 **Behavior Profiling:** Automated heuristics identifying suspicious behaviors: multi-day loitering, AIS manipulation (gaps), and zero-port evasive voyages.
- 📊 **Military-Grade Dashboard:** Built for operations rooms, featuring dynamic scrolling tickers, deep-linking, color-coded threat assessments, and map layers.
- 📋 **Tactical Exports:** One-click generation of `.txt` intelligence reports ready for legal documentation or naval interception briefings.
- 💬 **Conversational RAG:** Chat directly with the "OceanEye Intelligence Agent" to query specific vessel histories or summarize fleet deployments in human language.

---

## 🏗 System Architecture
OceanEye is built as a highly decoupled, stateless pipeline to ensure infinite scalability and stability:
* **Backend:** `FastAPI` (Python) deployed on **Google Cloud Run**. Completely stateless endpoints for risk calculation, chatting, and export generation.
* **Frontend:** Vanilla HTML/JS + `Leaflet.js` deployed on **Vercel** for instant delivery across the globe.
* **Intelligence Layer:** `Claude 3.5 Sonnet` via Anthropic API.
* **Data Sources:** `Global Fishing Watch` API (Vessel Metadata) + `AIS Stream` (Real-Time Location Data).

---

## 💻 Local Quickstart

### Prerequisites
1. Python 3.11+
2. Docker (Optional, for containerized run)
3. API Keys: Anthropic, Global Fishing Watch JWT, and AIS Stream Key.

### 1. Clone the repository
```bash
git clone https://github.com/Gastonchevarria/OceanEye.git
cd OceanEye
```

### 2. Configure Environment
```bash
cd backend
cp .env.example .env
```
Fill `.env` with your secure credentials:
```env
ANTHROPIC_API_KEY=sk-ant-...
GFW_API_TOKEN=eyJhbG...
AIS_STREAM_KEY=YOUR_KEY
FRONTEND_URL=http://localhost:3000
PORT=8000
```

### 3. Run the Backend API
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 4. Run the Frontend 
From the root of the project, spin up a simple static server:
```bash
cd frontend
python3 -m http.server 3000
```

Navigate to `http://localhost:3000` to access the Operations Dashboard.

---

## 🚀 Deployment (Production)

### Cloud Run (Backend)
```bash
cd backend
gcloud run deploy oceaneye-backend \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars ANTHROPIC_API_KEY=xxx,GFW_API_TOKEN=xxx
```

### Vercel (Frontend)
Point your Vercel project to the `frontend/` directory and ensure the `API_BASE` string in `index.html` matches your newly provisioned Cloud Run URL.

---

<div align="center">
  <p>🌍 <strong>Protecting our Oceans through Intelligence</strong></p>
  <sub>Built for the Hackathon Demo Day</sub>
</div>
