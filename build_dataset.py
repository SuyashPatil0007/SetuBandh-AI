import os
import pandas as pd
from sqlalchemy import text
from database import engine

print("[*] Starting dataset compilation from backend PostGIS records and arterial corridors...")

# 1. Fallback corridor registry if importing from main causes circular issues
CORRIDORS_DATA = [
    {"id": "c1", "name": "NH37 · Guwahati–Shillong", "tier": 1, "baseRisk": 12, "rainFactor": 0.35, "lat": 25.86, "lon": 91.81},
    {"id": "c2", "name": "NH15 · Guwahati–Tezpur", "tier": 1, "baseRisk": 10, "rainFactor": 0.25, "lat": 26.40, "lon": 92.26},
    {"id": "c3", "name": "NH13 · Tezpur–Bomdila–Itanagar", "tier": 1, "baseRisk": 42, "rainFactor": 0.95, "lat": 27.10, "lon": 92.80},
    {"id": "c4", "name": "NH52 · Tezpur–Dibrugarh", "tier": 1, "baseRisk": 15, "rainFactor": 0.30, "lat": 27.06, "lon": 93.85},
    {"id": "c5", "name": "AH1 · Itanagar–Dibrugarh", "tier": 1, "baseRisk": 22, "rainFactor": 0.40, "lat": 27.28, "lon": 94.25},
    {"id": "c6", "name": "NH27 · Guwahati–Silchar", "tier": 1, "baseRisk": 18, "rainFactor": 0.45, "lat": 25.48, "lon": 92.25},
    {"id": "c7", "name": "NH306 · Silchar–Aizawl", "tier": 1, "baseRisk": 28, "rainFactor": 0.55, "lat": 24.28, "lon": 92.74},
    {"id": "c8", "name": "NH37A · Silchar–Imphal", "tier": 2, "baseRisk": 30, "rainFactor": 0.60, "lat": 24.82, "lon": 93.35},
    {"id": "c9", "name": "NH29 · Guwahati–Dimapur–Kohima", "tier": 1, "baseRisk": 16, "rainFactor": 0.35, "lat": 25.90, "lon": 93.72},
    {"id": "c10", "name": "NH2 · Kohima–Imphal", "tier": 1, "baseRisk": 25, "rainFactor": 0.45, "lat": 25.24, "lon": 94.02},
    {"id": "c11", "name": "NH8 · Silchar–Agartala", "tier": 1, "baseRisk": 18, "rainFactor": 0.30, "lat": 24.33, "lon": 92.03},
    {"id": "c12", "name": "NH8 · Agartala–Aizawl", "tier": 2, "baseRisk": 22, "rainFactor": 0.35, "lat": 23.78, "lon": 92.00},
    {"id": "c13", "name": "NH10 · Siliguri–Gangtok", "tier": 1, "baseRisk": 35, "rainFactor": 0.85, "lat": 27.03, "lon": 88.50},
    {"id": "c14", "name": "NH27 · Siliguri–Guwahati", "tier": 1, "baseRisk": 14, "rainFactor": 0.20, "lat": 26.43, "lon": 90.06},
]

# Secondary and rural arterial connecting links
RURAL_BYPASSES = [
    {"id": "r1", "name": "Bhalukpong-Chaku Rural Arterial", "tier": 3, "baseRisk": 36, "rainFactor": 0.80, "lat": 27.01, "lon": 92.62},
    {"id": "r2", "name": "Jowai-Badarpur Bypass Link", "tier": 2, "baseRisk": 24, "rainFactor": 0.50, "lat": 25.20, "lon": 92.40},
    {"id": "r3", "name": "Teok-Mariani District Route", "tier": 3, "baseRisk": 18, "rainFactor": 0.30, "lat": 26.65, "lon": 94.30},
    {"id": "r4", "name": "Rangpo-Melli Rural Bypass", "tier": 2, "baseRisk": 32, "rainFactor": 0.75, "lat": 27.15, "lon": 88.52},
]

ALL_CORRIDORS = CORRIDORS_DATA + RURAL_BYPASSES

# 2. Query PostGIS for real hazard zone records and historical event counts
hazard_zones = []
try:
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT zone_name, hazard_type, risk_level, historical_event_count,
                   ST_Y(ST_Centroid(boundary)) AS lat, 
                   ST_X(ST_Centroid(boundary)) AS lon
            FROM hazard_zones;
        """)).mappings().all()
        hazard_zones = list(result)
        print(f"[+] Loaded {len(hazard_zones)} verified hazard zones from PostGIS.")
except Exception as e:
    print(f"[!] Notice: Could not read hazard_zones ({e}). Proceeding with corridor baseline attributes.")

# 3. Synthesize samples across varying rainfall distributions
records = []

for corridor in ALL_CORRIDORS:
    c_lat, c_lon = corridor["lat"], corridor["lon"]
    base_risk = corridor["baseRisk"]
    tier = corridor["tier"]
    rain_factor = corridor["rainFactor"]
    
    # Calculate nearest PostGIS hazard influence
    hist_events = 0
    multiplier = 1.0
    for hz in hazard_zones:
        distance_approx = ((hz["lat"] - c_lat) ** 2 + (hz["lon"] - c_lon) ** 2) ** 0.5
        if distance_approx < 0.6:  # Within ~60 km of known hazard zone
            hist_events += hz["historical_event_count"]
            if hz["risk_level"] == "CRITICAL":
                multiplier = max(multiplier, 1.45)
            elif hz["risk_level"] == "HIGH":
                multiplier = max(multiplier, 1.25)

    # Vary rainfall from light (10 mm) to extreme monsoon downpour (220 mm)
    for rainfall_mm in range(10, 230, 10):
        rain_term = (rainfall_mm * rain_factor) * 0.42
        tier_penalty = tier * 7.5
        history_penalty = min(28.0, hist_events * 3.2)
        
        raw_score = (base_risk * multiplier) + rain_term + tier_penalty + history_penalty
        final_risk = round(min(100.0, max(5.0, raw_score)), 2)
        
        records.append({
            "corridor_id": corridor["id"],
            "corridor_name": corridor["name"],
            "road_tier": tier,
            "rainfall_mm": float(rainfall_mm),
            "landslide_history": hist_events,
            "risk_score": final_risk
        })

# 4. Save to CSV
df = pd.DataFrame(records)
out_file = os.path.join(os.path.dirname(__file__), "road_features.csv")
df[["rainfall_mm", "road_tier", "landslide_history", "risk_score"]].to_csv(out_file, index=False)

print(f"[+] Successfully generated {len(df)} records.")
print(f"[+] Saved dataset to: {out_file}")