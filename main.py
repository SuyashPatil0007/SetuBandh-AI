import os
import json
import math
import asyncio
from typing import List, Optional, Dict, Any
import httpx
from fastapi import FastAPI, Depends, HTTPException, status, Query, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session
from geoalchemy2.functions import ST_SetSRID, ST_MakePoint

from database import engine, get_db, Base, SessionLocal
import models
import schemas
import telephony_services as telephony_service
from ai_engine import ai_hazard_predictor
from translation_services import translate_text

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Setubandh AI Core",
    description="Full-Scale Roadway Intelligence & Reactive WebSocket Mesh",
    version="4.5.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

REGIONAL_HUBS = {
    "GAU": {"name": "Guwahati", "lat": 26.1445, "lng": 91.7362, "district": "Kamrup Metro", "state": "Assam", "baseRisk": 15, "rainSens": 0.3},
    "SHL": {"name": "Shillong", "lat": 25.5788, "lng": 91.8933, "district": "East Khasi Hills", "state": "Meghalaya", "baseRisk": 20, "rainSens": 0.45},
    "TEZ": {"name": "Tezpur", "lat": 26.6528, "lng": 92.7926, "district": "Sonitpur", "state": "Assam", "baseRisk": 18, "rainSens": 0.35},
    "ITA": {"name": "Itanagar", "lat": 27.0844, "lng": 93.6053, "district": "Papum Pare", "state": "Arunachal", "baseRisk": 38, "rainSens": 0.95},
    "DIB": {"name": "Dibrugarh", "lat": 27.4728, "lng": 94.9120, "district": "Dibrugarh", "state": "Assam", "baseRisk": 14, "rainSens": 0.3},
    "SCH": {"name": "Silchar", "lat": 24.8333, "lng": 92.7789, "district": "Cachar", "state": "Assam", "baseRisk": 22, "rainSens": 0.55},
    "AIZ": {"name": "Aizawl", "lat": 23.7307, "lng": 92.7173, "district": "Aizawl", "state": "Mizoram", "baseRisk": 28, "rainSens": 0.6},
    "IMP": {"name": "Imphal", "lat": 24.8170, "lng": 93.9368, "district": "Imphal West", "state": "Manipur", "baseRisk": 30, "rainSens": 0.65},
    "KOH": {"name": "Kohima", "lat": 25.6751, "lng": 94.1086, "district": "Kohima", "state": "Nagaland", "baseRisk": 25, "rainSens": 0.5},
    "AGT": {"name": "Agartala", "lat": 23.8315, "lng": 91.2868, "district": "West Tripura", "state": "Tripura", "baseRisk": 18, "rainSens": 0.35},
    "GAN": {"name": "Gangtok", "lat": 27.3389, "lng": 88.6065, "district": "East Sikkim", "state": "Sikkim", "baseRisk": 35, "rainSens": 0.8},
    "SLG": {"name": "Siliguri", "lat": 26.7271, "lng": 88.3953, "district": "Gateway Corridors", "state": "West Bengal", "baseRisk": 15, "rainSens": 0.25}
}

VEHICLE_PHONE_DIRECTORY: Dict[str, str] = {
    "AS-01-EC-4412": "+919356467671",
    "NL-07-A-8901":  "+919405393846",
    "AR-02-B-1099":  "+919309008533",
    "MZ-01-T-7721":  "+918799978147",
    "MN-04-P-3342":  "+917219687205",
    "SK-03-C-5561":  "+919529415362",
}

DRIVER_PREFERRED_LANG: Dict[str, str] = {
    "AS-01-EC-4412": "as",
    "NL-07-A-8901":  "hi",
    "AR-02-B-1099":  "hi",
    "MZ-01-T-7721":  "en",
    "MN-04-P-3342":  "bn",
    "SK-03-C-5561":  "hi"
}

def query_local_osrm(coordinates: List[List[float]], alternatives: bool = False, exclude_highways: bool = False) -> tuple[List[dict], bool]:
    coord_str = ";".join([f"{lon},{lat}" for lat, lon in coordinates])
    alt_str = "true" if alternatives else "false"
    local_url = f"http://127.0.0.1:5000/route/v1/driving/{coord_str}?overview=full&geometries=geojson&alternatives={alt_str}"
    if exclude_highways:
        local_url += "&exclude=motorway,trunk"
    public_url = f"https://router.project-osrm.org/route/v1/driving/{coord_str}?overview=full&geometries=geojson&alternatives={alt_str}"

    for u, timeout_val in ((local_url, 0.15), (public_url, 1.8)):
        try:
            r = httpx.get(u, timeout=timeout_val)
            if r.status_code == 200:
                data = r.json()
                if data.get("routes") and len(data["routes"]) > 0:
                    routes = []
                    for rt in data["routes"]:
                        pts = [[p[1], p[0]] for p in rt["geometry"]["coordinates"]]
                        routes.append({
                            "waypoints": pts,
                            "distance_km": round(rt["distance"] / 1000.0, 1),
                            "duration_hrs": round(rt["duration"] / 3600.0, 1)
                        })
                    return routes, True
        except Exception:
            continue
    return [{"waypoints": coordinates, "distance_km": 60.0, "duration_hrs": 1.5}], False

def compute_tri_tier_routes(origin_key: str, dest_key: str, rain_val: float, lang: str = "en") -> Dict[str, Any]:
    o = REGIONAL_HUBS.get(origin_key, REGIONAL_HUBS["SHL"])
    d = REGIONAL_HUBS.get(dest_key, REGIONAL_HUBS["KOH"])
    corridor_label = f"{o['name']} → {d['name']}"

    routes, _ = query_local_osrm([[o['lat'], o['lng']], [d['lat'], d['lng']]], alternatives=False)
    primary_pts = routes[0]["waypoints"]
    primary_km = routes[0]["distance_km"]
    primary_hrs = routes[0]["duration_hrs"]

    step = max(1, len(primary_pts) // 20)
    sampled = primary_pts[::step]
    if primary_pts[-1] not in sampled:
        sampled.append(primary_pts[-1])
    wkt = f"SRID=4326;LINESTRING({', '.join([f'{p[1]} {p[0]}' for p in sampled])})"

    hist_count = 0
    obs_lat, obs_lon = primary_pts[len(primary_pts) // 2]

    with SessionLocal() as db:
        try:
            blocking_hazard = db.execute(text("""
                SELECT zone_name, risk_level, historical_event_count,
                       ST_Y(ST_Centroid(boundary)) as h_lat, ST_X(ST_Centroid(boundary)) as h_lon
                FROM hazard_zones
                WHERE ST_DWithin(boundary, ST_GeomFromEWKT(:wkt), 0.08)
                ORDER BY CASE WHEN risk_level = 'CRITICAL' THEN 1 ELSE 2 END
                LIMIT 1;
            """), {"wkt": wkt}).mappings().first()
            if blocking_hazard:
                hist_count = blocking_hazard["historical_event_count"]
                obs_lat = blocking_hazard["h_lat"]
                obs_lon = blocking_hazard["h_lon"]
        except Exception:
            pass

    risk_primary = int(ai_hazard_predictor.predict_risk(rainfall_mm=rain_val, road_tier=1, landslide_history=hist_count))
    risk_detour1 = int(ai_hazard_predictor.predict_risk(rainfall_mm=rain_val * 0.85, road_tier=2, landslide_history=max(0, hist_count - 2)))
    risk_detour2 = int(ai_hazard_predictor.predict_risk(rainfall_mm=rain_val * 0.65, road_tier=3, landslide_history=0))

    tier1_blocked = risk_primary >= 45 or rain_val >= 45
    tier2_blocked = risk_detour1 >= 48 or rain_val >= 55

    dx = d['lng'] - o['lng']
    dy = d['lat'] - o['lat']
    length = math.hypot(dx, dy) or 1.0

    bypass1_lat = round(obs_lat - (dx / length) * 0.35, 5)
    bypass1_lon = round(obs_lon + (dy / length) * 0.35, 5)
    detour1_res, _ = query_local_osrm([[o['lat'], o['lng']], [bypass1_lat, bypass1_lon], [d['lat'], d['lng']]])

    bypass2_lat = round(obs_lat - (dx / length) * 0.68, 5)
    bypass2_lon = round(obs_lon + (dy / length) * 0.68, 5)
    detour2_res, _ = query_local_osrm([[o['lat'], o['lng']], [bypass2_lat, bypass2_lon], [d['lat'], d['lng']]])

    route_primary = {
        "id": "route_direct",
        "name": f"Direct Highway: {corridor_label}",
        "tier": "Primary Trunk",
        "risk_score": risk_primary,
        "distance_km": primary_km,
        "estimated_hours": primary_hrs,
        "status": "BLOCKED" if tier1_blocked else "OPTIMAL",
        "waypoints": primary_pts
    }

    route_detour1 = {
        "id": "route_bypass1",
        "name": "Secondary Arterial Bypass (Valley Route)",
        "tier": "State Secondary Highway",
        "risk_score": risk_detour1,
        "distance_km": detour1_res[0]["distance_km"],
        "estimated_hours": detour1_res[0]["duration_hrs"],
        "status": "BLOCKED" if tier2_blocked else ("ACTIVE_DETOUR" if tier1_blocked else "STANDBY"),
        "waypoints": detour1_res[0]["waypoints"]
    }

    route_detour2 = {
        "id": "route_bypass2",
        "name": "Outer Emergency Lifeline (High-Ground Ridge)",
        "tier": "Regional Collector Bypass",
        "risk_score": risk_detour2,
        "distance_km": detour2_res[0]["distance_km"],
        "estimated_hours": detour2_res[0]["duration_hrs"],
        "status": "ACTIVE_DETOUR" if tier2_blocked else "STANDBY",
        "waypoints": detour2_res[0]["waypoints"]
    }

    if tier2_blocked:
        active_rec = route_detour2
        raw_reason = f"Severe Rainfall Breach ({rain_val} mm): Direct Highway & Valley Bypass Blocked. Re-routing to Outer Lifeline."
    elif tier1_blocked:
        active_rec = route_detour1
        raw_reason = f"Rainfall Trigger 1 Breach ({rain_val} mm): Direct Highway at Critical Risk ({risk_primary}/100). Valley Bypass Active."
    else:
        active_rec = route_primary
        raw_reason = "All Corridors Safe & Passable."

    return {
        "corridor_name": corridor_label,
        "origin_key": origin_key,
        "dest_key": dest_key,
        "origin_coord": [o['lat'], o['lng']],
        "dest_coord": [d['lat'], d['lng']],
        "rain_intensity": rain_val,
        "reroute_required": tier1_blocked,
        "active_trigger_level": 2 if tier2_blocked else (1 if tier1_blocked else 0),
        "blockage_reason": raw_reason,
        "primary_route": route_primary,
        "suggested_detour": active_rec if tier1_blocked else None,
        "all_routes": [route_primary, route_detour1, route_detour2]
    }

# Central Synchronized State Hub
class ReactiveHub:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.origin_key: str = "SHL"
        self.dest_key: str = "KOH"
        self.rain_mm: float = 45.0
        self.lang: str = "en"

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active_connections.append(ws)
        payload = compute_tri_tier_routes(self.origin_key, self.dest_key, self.rain_mm, self.lang)
        payload["blockage_reason"] = await translate_text(payload["blockage_reason"], target_lang=self.lang)
        await ws.send_json({"type": "SYNC_STATE", "payload": payload})

    def disconnect(self, ws: WebSocket):
        if ws in self.active_connections:
            self.active_connections.remove(ws)

    async def broadcast_mutation(self):
        payload = compute_tri_tier_routes(self.origin_key, self.dest_key, self.rain_mm, self.lang)
        payload["blockage_reason"] = await translate_text(payload["blockage_reason"], target_lang=self.lang)
        dead = []
        for c in self.active_connections:
            try:
                await c.send_json({"type": "SYNC_STATE", "payload": payload})
            except Exception:
                dead.append(c)
        for d in dead:
            self.disconnect(d)

    async def broadcast_incident(self, incident: dict):
        dead = []
        for c in self.active_connections:
            try:
                await c.send_json({"type": "INCIDENT_ALERT", "incident": incident})
            except Exception:
                dead.append(c)
        for d in dead:
            self.disconnect(d)

reactive_hub = ReactiveHub()

@app.websocket("/ws/simulation")
async def websocket_mesh(ws: WebSocket):
    await reactive_hub.connect(ws)
    try:
        while True:
            data = await ws.receive_json()
            action = data.get("action")
            if action == "SET_CORRIDOR":
                reactive_hub.origin_key = data.get("from", reactive_hub.origin_key)
                reactive_hub.dest_key = data.get("to", reactive_hub.dest_key)
                await reactive_hub.broadcast_mutation()
            elif action == "SET_RAIN":
                reactive_hub.rain_mm = float(data.get("rain_mm", reactive_hub.rain_mm))
                await reactive_hub.broadcast_mutation()
            elif action == "SET_LANG":
                reactive_hub.lang = data.get("lang", "en")
                await reactive_hub.broadcast_mutation()
    except WebSocketDisconnect:
        reactive_hub.disconnect(ws)

# Direct HTML File Loader with Fallback Detection
def load_html_content(candidate_filenames: List[str]) -> str:
    for filename in candidate_filenames:
        target_path = os.path.join(BASE_DIR, filename)
        if os.path.isfile(target_path):
            with open(target_path, "r", encoding="utf-8") as f:
                return f.read()
    raise HTTPException(
        status_code=404,
        detail=f"Template file not found. Tried {candidate_filenames} in {BASE_DIR}"
    )

@app.get("/admin", response_class=HTMLResponse)
def serve_admin():
    content = load_html_content(["ner2.html", "ner2_2.html", "ner2_3.html"])
    return HTMLResponse(content=content)

@app.get("/driver", response_class=HTMLResponse)
def serve_driver():
    content = load_html_content(["nertrial.html", "nertrial_2.html"])
    return HTMLResponse(content=content)

# REST Endpoints
class DynamicRouteRequest(BaseModel):
    origin_name: str
    dest_name: str
    origin_lat: float
    origin_lon: float
    dest_lat: float
    dest_lon: float
    rain_intensity: int = 45
    preferred_lang: str = "en"

@app.post("/api/routing/dynamic-detour", tags=["Routing"])
async def route_with_bidirectional_detour(req: DynamicRouteRequest):
    o_key = "SHL"
    d_key = "KOH"
    for k, v in REGIONAL_HUBS.items():
        if abs(v['lat'] - req.origin_lat) < 0.1 and abs(v['lng'] - req.origin_lon) < 0.1:
            o_key = k
        if abs(v['lat'] - req.dest_lat) < 0.1 and abs(v['lng'] - req.dest_lon) < 0.1:
            d_key = k

    reactive_hub.origin_key = o_key
    reactive_hub.dest_key = d_key
    reactive_hub.rain_mm = float(req.rain_intensity)
    reactive_hub.lang = req.preferred_lang

    payload = compute_tri_tier_routes(o_key, d_key, reactive_hub.rain_mm, reactive_hub.lang)
    payload["blockage_reason"] = await translate_text(payload["blockage_reason"], target_lang=req.preferred_lang)
    await reactive_hub.broadcast_mutation()
    return payload

@app.post(
    "/api/telemetry/pings",
    response_model=schemas.UserLocationPingResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Telemetry"],
)
async def record_user_gps(
    ping: schemas.UserLocationPingCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    db_ping = models.UserLocationPing(
        user_id=ping.user_id,
        speed_kmh=ping.speed_kmh,
        heading=ping.heading,
        location=ST_SetSRID(ST_MakePoint(ping.longitude, ping.latitude), 4326),
    )
    db.add(db_ping)
    db.commit()
    db.refresh(db_ping)

    coords = db.execute(
        text("SELECT ST_Y(location) AS lat, ST_X(location) AS lon FROM user_location_pings WHERE id = :id"),
        {"id": db_ping.id},
    ).mappings().first()

    threat_query = text("""
        SELECT incident_type, description,
               ST_Distance(location, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)) * 111000.0 as dist_meters
        FROM incident_reports
        WHERE ST_DWithin(location, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326), 0.135)
        ORDER BY created_at DESC
        LIMIT 1;
    """)
    nearby_threat = db.execute(threat_query, {"lat": ping.latitude, "lon": ping.longitude}).mappings().first()

    if nearby_threat and ping.user_id in VEHICLE_PHONE_DIRECTORY:
        target_phone = VEHICLE_PHONE_DIRECTORY[ping.user_id]
        dist_km = round(nearby_threat["dist_meters"] / 1000.0, 1)
        driver_lang = DRIVER_PREFERRED_LANG.get(ping.user_id, "en")

        detour_text = await translate_text("Local Arterial Bypass", target_lang=driver_lang)

        background_tasks.add_task(
            telephony_service.send_driver_sms,
            to_phone=target_phone,
            vehicle_id=ping.user_id,
            hazard_type=nearby_threat["incident_type"],
            corridor_name=f"Roadway ahead ({dist_km} km)",
            detour_info=detour_text
        )
        background_tasks.add_task(
            telephony_service.dispatch_driver_call,
            to_phone=target_phone,
            vehicle_id=ping.user_id,
            hazard_type=nearby_threat["incident_type"],
            detour_info=detour_text
        )

    return schemas.UserLocationPingResponse(
        id=db_ping.id,
        user_id=db_ping.user_id,
        latitude=coords["lat"],
        longitude=coords["lon"],
        speed_kmh=db_ping.speed_kmh,
        heading=db_ping.heading,
        recorded_at=db_ping.recorded_at,
    )

@app.post("/api/incidents", status_code=status.HTTP_201_CREATED, tags=["Incidents"])
async def report_incident(
    report: schemas.CrowdIncidentReportCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    db_report = models.CrowdIncidentReport(
        reporter_id=report.reporter_id,
        incident_type=report.incident_type.upper(),
        severity=report.severity.upper(),
        description=report.description,
        location=ST_SetSRID(ST_MakePoint(report.longitude, report.latitude), 4326)
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)

    incident_payload = {
        "id": db_report.id,
        "incident_type": db_report.incident_type,
        "severity": db_report.severity,
        "description": db_report.description,
        "latitude": report.latitude,
        "longitude": report.longitude,
        "created_at": "Just now"
    }
    background_tasks.add_task(reactive_hub.broadcast_incident, incident_payload)
    return {"status": "SUCCESS", "id": db_report.id}

@app.get("/api/telemetry/active-fleet", response_model=List[schemas.UserLocationPingResponse], tags=["Telemetry"])
def get_active_fleet(db: Session = Depends(get_db)):
    records = db.execute(text("""
        SELECT DISTINCT ON (user_id) id, user_id, ST_Y(location) AS lat, ST_X(location) AS lon, speed_kmh, heading, recorded_at
        FROM user_location_pings ORDER BY user_id, recorded_at DESC;
    """)).mappings().all()
    return [
        schemas.UserLocationPingResponse(
            id=r["id"], user_id=r["user_id"], latitude=r["lat"], longitude=r["lon"],
            speed_kmh=r["speed_kmh"], heading=r["heading"], recorded_at=r["recorded_at"]
        ) for r in records
    ]

@app.get("/api/weather/live-corridor-risk", tags=["Weather"])
async def get_live_weather():
    max_precip = 0.0
    async with httpx.AsyncClient(timeout=4.0) as client:
        for _, coords in REGIONAL_HUBS.items():
            url = f"https://api.open-meteo.com/v1/forecast?latitude={coords['lat']}&longitude={coords['lng']}&current=precipitation,rain"
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json().get("current", {})
                    precip = data.get("precipitation", 0.0)
                    max_precip = max(max_precip, precip)
            except Exception:
                continue
    derived_index = min(100, int((max_precip / 15.0) * 100)) if max_precip > 0 else 45
    return {
        "status": "ONLINE",
        "regional_rainfall_index": max(derived_index, 45),
        "peak_precipitation_mm": max_precip or 18.5,
        "critical_alert": max_precip >= 10.0
    }

@app.get("/api/hazard-zones/geojson", tags=["Spatial Analytics"])
def get_hazard_zones_geojson(db: Session = Depends(get_db)) -> Dict[str, Any]:
    rows = db.execute(text(
        "SELECT id, zone_name, hazard_type, risk_level, historical_event_count, "
        "ST_AsGeoJSON(boundary) AS geojson_geom FROM hazard_zones;"
    )).mappings().all()
    
    features = []
    for r in rows:
        if r["geojson_geom"]:
            features.append({
                "type": "Feature",
                "id": r["id"],
                "geometry": json.loads(r["geojson_geom"]),
                "properties": {
                    "zone_name": r["zone_name"],
                    "hazard_type": r["hazard_type"],
                    "risk_level": r["risk_level"],
                    "historical_event_count": r["historical_event_count"]
                }
            })
    return {"type": "FeatureCollection", "features": features}

@app.get("/api/db/test-postgis", tags=["System"])
def test_postgis(db: Session = Depends(get_db)):
    version = db.execute(text("SELECT PostGIS_Full_Version();")).scalar()
    return {"status": "CONNECTED", "postgis_version": version}