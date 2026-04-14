"""
OceanEye Backend v3 — Real-Time Maritime Intelligence Platform
FastAPI + Claude AI + aisstream.io WebSocket + Global Fishing Watch
"""

import os
import json
import math
import random
import logging
import asyncio
from datetime import datetime, timedelta

import httpx
import anthropic
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# ─── Config ────────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GFW_API_TOKEN = os.getenv("GFW_API_TOKEN", "")
AIS_STREAM_KEY = os.getenv("AIS_STREAM_KEY", "")
GFW_BASE_URL = "https://gateway.api.globalfishingwatch.org/v3"
PORT = int(os.getenv("PORT", 8000))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("oceaneye")

# ─── Demo Vessels ──────────────────────────────────────────────────────────────
DEMO_VESSELS = [
    {
        "mmsi": "577317000", "name": "Bao Feng", "flag": "Vanuatu",
        "vessel_type": "Squid Jigger",
        "gfw_id": "2b0234f60-0239-e83b-dfc8-101c4055faf4",
        "lat": -46.5, "lon": -59.2, "heading": 215,
        "risk_score": 97, "risk_label": "critical",
        "events_summary": "Fined $1.260M for illegal fishing in Argentina EEZ Jan 2026",
        "loitering_count": 98, "port_visits": 0, "ais_gaps": 14,
        "avg_speed": 2.1, "zone": "South Atlantic – Argentina EEZ border",
        "known_violations": ["Fined $1.260M (Jan 2026)", "AIS manipulation", "Unauthorized EEZ entry"],
        "trail": [{"lat":-45.8,"lon":-58.0},{"lat":-46.0,"lon":-58.5},{"lat":-46.2,"lon":-58.9},{"lat":-46.4,"lon":-59.1},{"lat":-46.5,"lon":-59.2}],
        "trips": 5, "ais_transmissions": 172163,
    },
    {
        "mmsi": "577038000", "name": "Hai Xing 2", "flag": "Vanuatu",
        "vessel_type": "Trawler",
        "gfw_id": "ad7b81e13-3729-c048-6dab-791e202f21c0",
        "lat": -45.8, "lon": -62.1, "heading": 165,
        "risk_score": 94, "risk_label": "critical",
        "events_summary": "2025 vessel, first voyage = illegal fishing Argentina EEZ. 88 loitering events. 0 port visits. Suspected IUU fleet member.",
        "loitering_count": 88, "port_visits": 0, "ais_gaps": 9,
        "avg_speed": 1.8, "zone": "South Atlantic – Argentina EEZ",
        "known_violations": ["Illegal fishing in EEZ (2025)", "Zero port compliance", "Fleet coordination suspected"],
        "trail": [{"lat":-44.9,"lon":-61.2},{"lat":-45.1,"lon":-61.5},{"lat":-45.4,"lon":-61.8},{"lat":-45.6,"lon":-62.0},{"lat":-45.8,"lon":-62.1}],
    },
    {
        "mmsi": "412329686", "name": "Lu Qing Yuan Yu 205", "flag": "China",
        "vessel_type": "Squid Jigger",
        "gfw_id": "c69320602-2c89-eb82-150f-bb70fa6ced91",
        "lat": -44.5, "lon": -56.0, "heading": 280,
        "risk_score": 92, "risk_label": "critical",
        "events_summary": "343 high seas encounters — transshipment network. Illegal mapping of Continental Shelf",
        "loitering_count": 42, "port_visits": 2, "ais_gaps": 5,
        "avg_speed": 3.4, "zone": "South Atlantic – Agujero Azul",
        "known_violations": ["343 high seas encounters", "Illegal continental shelf mapping"],
        "trail": [{"lat":-44.0,"lon":-55.0},{"lat":-44.1,"lon":-55.3},{"lat":-44.3,"lon":-55.6},{"lat":-44.4,"lon":-55.8},{"lat":-44.5,"lon":-56.0}],
        "fishing_hours": 50878, "encounters": 343, "trips": 36, "ais_transmissions": 3359672,
    },
    {
        "mmsi": "412549383", "name": "Lu Rong Yuan Yu 668", "flag": "China",
        "vessel_type": "Squid Jigger", "gfw_id": "demo-lurongyuanyu-668",
        "lat": -43.2, "lon": -58.7, "heading": 190,
        "risk_score": 88, "risk_label": "critical",
        "events_summary": "Fled Coast Guard GC-27 refusing boarding Apr 2020",
        "loitering_count": 35, "port_visits": 0, "ais_gaps": 8,
        "avg_speed": 3.8, "zone": "South Atlantic – EEZ boundary",
        "known_violations": ["Fled Coast Guard GC-27 (Apr 2020)"],
        "trail": [{"lat":-42.5,"lon":-58.0},{"lat":-42.7,"lon":-58.2},{"lat":-42.9,"lon":-58.4},{"lat":-43.1,"lon":-58.6},{"lat":-43.2,"lon":-58.7}],
        "fishing_hours": 15309, "encounters": 30, "trips": 15, "mpas_violated": 3,
    },
    {
        "mmsi": "416002790", "name": "Shun Li 8", "flag": "Taiwan",
        "vessel_type": "Longliner", "gfw_id": "demo-shunli-8",
        "lat": -47.1, "lon": -60.5, "heading": 135,
        "risk_score": 65, "risk_label": "suspicious",
        "events_summary": "Suspected transshipment activity. 28 loitering events. 1 port visit in 6 months.",
        "loitering_count": 28, "port_visits": 1, "ais_gaps": 3,
        "avg_speed": 4.2, "zone": "South Atlantic – High Seas",
        "known_violations": ["Suspected transshipment", "Minimal port compliance"],
        "trail": [{"lat":-46.4,"lon":-59.6},{"lat":-46.6,"lon":-59.9},{"lat":-46.8,"lon":-60.1},{"lat":-47.0,"lon":-60.3},{"lat":-47.1,"lon":-60.5}],
    },
    {
        "mmsi": "601234567", "name": "Mar del Plata VII", "flag": "Argentina",
        "vessel_type": "Trawler", "gfw_id": "demo-mardelplata-7",
        "lat": -42.8, "lon": -57.3, "heading": 45,
        "risk_score": 15, "risk_label": "normal",
        "events_summary": "Licensed Argentine fishing vessel. Regular port visits. No AIS gaps. Full compliance.",
        "loitering_count": 5, "port_visits": 12, "ais_gaps": 0,
        "avg_speed": 6.5, "zone": "Argentina EEZ – Licensed",
        "known_violations": [],
        "trail": [{"lat":-42.3,"lon":-56.8},{"lat":-42.4,"lon":-56.9},{"lat":-42.6,"lon":-57.1},{"lat":-42.7,"lon":-57.2},{"lat":-42.8,"lon":-57.3}],
    },
    {
        "mmsi": "601987654", "name": "Esperanza Sur", "flag": "Argentina",
        "vessel_type": "Longliner", "gfw_id": "demo-esperanza-sur",
        "lat": -44.0, "lon": -61.0, "heading": 320,
        "risk_score": 22, "risk_label": "normal",
        "events_summary": "Compliant vessel with full documentation. Regular schedule. All AIS active.",
        "loitering_count": 8, "port_visits": 10, "ais_gaps": 0,
        "avg_speed": 7.1, "zone": "Argentina EEZ – Licensed",
        "known_violations": [],
        "trail": [{"lat":-43.4,"lon":-60.5},{"lat":-43.5,"lon":-60.6},{"lat":-43.7,"lon":-60.8},{"lat":-43.9,"lon":-60.9},{"lat":-44.0,"lon":-61.0}],
    },
    {
        "mmsi": "538007430", "name": "Oryong 373", "flag": "South Korea",
        "vessel_type": "Trawler", "gfw_id": "demo-oryong-373",
        "lat": -45.3, "lon": -55.8, "heading": 250,
        "risk_score": 48, "risk_label": "normal",
        "events_summary": "Moderate activity near Falklands. Licensed in adjacent zone. Previous incident in 2016.",
        "loitering_count": 18, "port_visits": 5, "ais_gaps": 1,
        "avg_speed": 5.0, "zone": "South Atlantic – Falklands adjacent",
        "known_violations": ["Minor infraction 2016 (resolved)"],
        "trail": [{"lat":-44.8,"lon":-55.0},{"lat":-44.9,"lon":-55.2},{"lat":-45.1,"lon":-55.4},{"lat":-45.2,"lon":-55.6},{"lat":-45.3,"lon":-55.8}],
    },
]


app = FastAPI(
    title="OceanEye API",
    description="Real-time maritime intelligence — v3",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Models ────────────────────────────────────────────────────────────────────
class VesselData(BaseModel):
    mmsi: str
    name: str
    flag: str
    loitering_count: int = 0
    port_visits: int = 0
    ais_gaps: int = 0
    avg_speed: float = 0.0
    zone: str = "South Atlantic"

class AnalyzeRequest(BaseModel):
    vessel_data: VesselData

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    conversation_history: list[ChatMessage] = []

class ExportRequest(BaseModel):
    vessel_data: dict
    claude_report: dict


def get_claude_client():
    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured")
    return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


# ─── Tool execution ───────────────────────────────────────────────────────────
def execute_tool(tool_name: str, tool_input: dict) -> str:
    if tool_name == "get_vessels":
        return json.dumps(DEMO_VESSELS, ensure_ascii=False)
    elif tool_name == "search_by_flag":
        flag = tool_input.get("flag", "").lower()
        results = [v for v in DEMO_VESSELS if v["flag"].lower() == flag]
        if not results:
            return json.dumps({"message": f"No vessels found with flag '{flag}'", "available_flags": list(set(v["flag"] for v in DEMO_VESSELS))})
        return json.dumps(results, ensure_ascii=False)
    elif tool_name == "get_zone_summary":
        critical = [v for v in DEMO_VESSELS if v["risk_score"] >= 75]
        suspicious = [v for v in DEMO_VESSELS if 50 <= v["risk_score"] < 75]
        normal = [v for v in DEMO_VESSELS if v["risk_score"] < 50]
        return json.dumps({
            "zone": "South Atlantic – Argentina EEZ Region",
            "total_vessels": len(DEMO_VESSELS),
            "threat_level": "HIGH" if len(critical) >= 2 else "MODERATE",
            "critical_count": len(critical), "suspicious_count": len(suspicious), "normal_count": len(normal),
            "flags_present": list(set(v["flag"] for v in DEMO_VESSELS)),
            "avg_risk_score": round(sum(v["risk_score"] for v in DEMO_VESSELS) / len(DEMO_VESSELS), 1),
            "top_threats": [{"name": v["name"], "flag": v["flag"], "risk": v["risk_score"], "summary": v["events_summary"]} for v in critical],
            "ais_stream_active": True,
            "live_vessels_count": 0,
            "total_ais_messages": 0,
        }, ensure_ascii=False)
    return json.dumps({"error": f"Unknown tool: {tool_name}"})


CHAT_TOOLS = [
    {
        "name": "get_vessels",
        "description": "Get all tracked vessels with positions, risk scores, activity indicators, and event summaries.",
        "input_schema": {"type": "object", "properties": {"zone": {"type": "string", "default": "south_atlantic"}}, "required": []},
    },
    {
        "name": "search_by_flag",
        "description": "Search vessels by flag state (country). E.g. 'China', 'Vanuatu', 'Argentina'.",
        "input_schema": {"type": "object", "properties": {"flag": {"type": "string"}}, "required": ["flag"]},
    },
    {
        "name": "get_zone_summary",
        "description": "Get threat assessment: risk levels, vessel counts, top threats, AIS stream status, IUU hotspots.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]

SYSTEM_PROMPT = """You are an OceanEye maritime intelligence analyst.
Monitored Area: South Atlantic — Argentina EEZ Border (Mile 200-220)

Critical Context:
- The Chinese fleet accounts for 66% of all AIS gap events at the EEZ border
- +600,000 hours of unbroadcasted fishing documented (dark vessels)
- Gaps are concentrated exactly between miles 200-220
- Operation Mare Nostrum I active (Argentine Navy, 2025/2026)
- The Blue Hole (43°-47°S): maximum squid concentration zone

Always respond in English. Be direct. Never say 'it could be' — 
take a firm position based on data."""

CHAT_SYSTEM_PROMPT = SYSTEM_PROMPT + """

Always use tools to fetch data before answering. Be specific with MMSI, coordinates, risk scores.
Respond ONLY in English. Use markdown for clarity."""


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/")
async def root():
    return {
        "app": "OceanEye API",
        "version": "3.0",
        "status": "online",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/config")
async def get_client_config():
    return {"ais_stream_key": AIS_STREAM_KEY}

async def get_claude_risk(v: dict):
    def _call():
        client = get_claude_client()
        prompt = f"Given these data, calculate the risk score. Respond ONLY with JSON:\n{{\"risk_score\": int, \"risk_label\": \"CRITICAL|HIGH|MEDIUM|LOW\", \"risk_color\": \"#ef4444|#f97316|#f59e0b|#22c55e\"}}\nData: {json.dumps(v)}"
        try:
            resp = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=150,
                messages=[{"role": "user", "content": prompt}]
            )
            text = resp.content[0].text.strip()
            # clean json
            if "{" in text: text = "{" + text.split("{", 1)[1]
            if "}" in text: text = text.rsplit("}", 1)[0] + "}"
            return json.loads(text)
        except Exception as e:
            return None

    result = await asyncio.to_thread(_call)
    v_copy = v.copy()
    if result and isinstance(result, dict) and "risk_score" in result:
        v_copy["risk_score"] = result.get("risk_score", v.get("risk_score", 0))
        v_copy["risk_label"] = result.get("risk_label", v.get("risk_label", "UNKNOWN"))
        v_copy["risk_color"] = result.get("risk_color", "#94a3b8")
        v_copy["claude_ai_score"] = True
    else:
        v_copy["claude_ai_score"] = False
    return v_copy

@app.get("/vessels")
async def get_vessels(zone: str = "south_atlantic"):
    tasks = [get_claude_risk(v) for v in DEMO_VESSELS]
    results = await asyncio.gather(*tasks)
    return {"vessels": results, "source": "demo_data_with_claude_risk"}


@app.get("/vessel/{mmsi}/events")
async def get_vessel_events(mmsi: str):
    """Fetch real events from GFW API for a specific vessel."""
    vessel = next((v for v in DEMO_VESSELS if v["mmsi"] == mmsi), None)

    if not vessel or not GFW_API_TOKEN:
        return {"events": [], "source": "not_available"}

    gfw_id = vessel.get("gfw_id", "")
    if gfw_id.startswith("demo-"):
        return {"events": [], "source": "demo_vessel"}

    headers = {"Authorization": f"Bearer {GFW_API_TOKEN}"}
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{GFW_BASE_URL}/events",
                params={
                    "vessels[0]": gfw_id,
                    "datasets[0]": "public-global-loitering-events:latest",
                    "datasets[1]": "public-global-gaps-events:latest",
                    "datasets[2]": "public-global-fishing-events:latest",
                    "start-date": start_date,
                    "end-date": end_date,
                    "limit": 50,
                },
                headers=headers,
            )
            if resp.status_code == 200:
                data = resp.json()
                return {"events": data.get("entries", data if isinstance(data, list) else []), "source": "gfw_api"}
            else:
                logger.warning(f"GFW events {resp.status_code}: {resp.text[:200]}")
                return {"events": [], "source": "gfw_error", "status": resp.status_code}
    except Exception as e:
        logger.warning(f"GFW events error: {e}")
        return {"events": [], "source": "error"}


@app.post("/analyze")
async def analyze_vessel(request: AnalyzeRequest):
    vessel = request.vessel_data
    prompt = SYSTEM_PROMPT + f"""

Analizá este barco y generá un informe JSON estructurado.

Datos del barco:
- MMSI: {vessel.mmsi} | Vessel Name: {vessel.name} | Flag: {vessel.flag}
- Loitering count: {vessel.loitering_count} | Port visits: {vessel.port_visits}
- AIS gaps: {vessel.ais_gaps} | Avg Speed: {vessel.avg_speed} kn | Zone: {vessel.zone}

Criterios: loitering>30=suspicious, ports=0=evasion, AIS gaps>3=dark vessel, speed<3kn=trawling.
If you consider the risk score is LOW (<40), the "summary" MUST strictly include the phrase: "No signs of illegal activity detected. Operating pattern within normal parameters."

Respond SOLO with a valid JSON, no extra text, no markdown, matching this exact structure:
{{
  "risk_score": <int>,
  "risk_label": "<CRITICAL|HIGH|MEDIUM|LOW>",
  "risk_color": "<#ef4444|#f97316|#f59e0b|#22c55e>",
  "summary": "<2-3 english sentences>",
  "red_flags": ["<list>", "<of>", "<behaviors>"],
  "most_suspicious": "<the most suspicious trait in 1 sentence>",
  "recommendation": "<concrete action to take>"
}}"""

    def call_claude(content: str):
        client = get_claude_client()
        msg = client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=1024,
            messages=[{"role": "user", "content": content}]
        )
        t = msg.content[0].text.strip()
        if t.startswith("```"):
            t = t.split("```")[1]
            if t.startswith("json"): t = t[4:]
            t = t.strip()
        return t

    try:
        text = call_claude(prompt)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Retry once
            retry_prompt = text + "\n\nError: Invalid JSON. Respondé SOLO con JSON válido, sin texto extra, sin markdown."
            text2 = call_claude(retry_prompt)
            return json.loads(text2)
            
    except json.JSONDecodeError:
        return {
            "risk_score": 50,
            "risk_label": "MEDIUM",
            "risk_color": "#f59e0b",
            "summary": "No se pudo codificar el JSON correctamente.",
            "red_flags": [],
            "most_suspicious": "Análisis fallido",
            "recommendation": "Revisión manual"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat")
async def chat_with_agent(request: ChatRequest):
    # Chat logic identical to before
    try:
        user_message = request.message
        history = [{"role": m.role, "content": m.content} for m in request.conversation_history[-8:]]
        
        messages = history + [{"role": "user", "content": user_message}]
        
        client = get_claude_client()
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=CHAT_SYSTEM_PROMPT,
            messages=messages,
            tools=CHAT_TOOLS,
        )
        
        tools_used = []
        for _ in range(3):
            if response.stop_reason != "tool_use":
                break
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    tools_used.append({"name": block.name, "params": block.input})
                    tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": execute_tool(block.name, block.input)})

            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
            response = client.messages.create(model="claude-sonnet-4-20250514", max_tokens=2048, system=CHAT_SYSTEM_PROMPT, tools=CHAT_TOOLS, messages=messages)

        reply = "".join(b.text for b in response.content if b.type == "text")
        return {"reply": reply, "tools_used": tools_used or None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/export")
async def generate_export(request: ExportRequest):
    v = request.vessel_data
    cr = request.claude_report
    now_utc = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    
    prompt = f"""Generate a plain text report for the vessel {v.get('name')}.
Replace brackets with provided data keeping this exact format:

OCEANEYE — MARITIME INTELLIGENCE REPORT
Generated: {now_utc}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VESSEL: {v.get('name')} | MMSI: {v.get('mmsi')} | FLAG: {v.get('flag')}
RISK SCORE: {v.get('risk_score', '0')}/100 — {str(v.get('risk_label', 'UNKNOWN')).upper()}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANALYSIS: {cr.get('summary', '')}
RED FLAGS:
{chr(10).join(['- ' + str(rf) for rf in cr.get('red_flags', [])])}
MOST SUSPICIOUS: {cr.get('most_suspicious', '')}
RECOMMENDED ACTION: {cr.get('recommendation', '')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Powered by Claude AI (Anthropic) + Global Fishing Watch"""

    def _call():
        client = get_claude_client()
        msg = client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        return msg.content[0].text.strip()
    
    try:
        text = await asyncio.to_thread(_call)
        return {"report": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/briefing")
async def generate_briefing():
    zone_data = execute_tool("get_zone_summary", {})
    prompt = SYSTEM_PROMPT + f"""

Generate a concise DAILY INTELLIGENCE BRIEFING.

Data: {zone_data}

Format: 1. THREAT LEVEL (1 line) 2. KEY FINDINGS (2-3 bullets) 3. IMMEDIATE ACTIONS (1-2 bullets)
Under 150 words. Authoritative, direct. Use markdown. No headers."""

    try:
        client = get_claude_client()
        msg = client.messages.create(model="claude-sonnet-4-20250514", max_tokens=512, messages=[{"role": "user", "content": prompt}])
        return {"briefing": msg.content[0].text.strip(), "generated_at": datetime.now().isoformat(), "ais_active": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
