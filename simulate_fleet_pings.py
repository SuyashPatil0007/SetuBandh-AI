import time
import math
import requests

API_URL = "http://127.0.0.1:8000/api/telemetry/pings"

ROUTES = {
    "c1": [(26.1445, 91.7362), (26.0600, 91.8100), (25.9030, 91.8810), (25.7500, 91.9050), (25.6600, 91.9000), (25.5788, 91.8933)],
    "c3": [(26.6528, 92.7926), (26.8500, 92.7000), (27.0100, 92.6400), (27.1600, 92.4200), (27.2600, 92.4200), (27.1500, 92.9000), (27.1000, 93.2000), (27.0844, 93.6053)],
    "c7": [(24.8333, 92.7789), (24.5800, 92.7400), (24.2300, 92.6800), (23.9500, 92.6900), (23.7307, 92.7173)],
    "c8": [(24.8333, 92.7789), (24.8000, 93.1200), (24.7800, 93.4500), (24.8200, 93.7000), (24.8170, 93.9368)],
    "c9": [(26.1445, 91.7362), (26.3500, 92.6800), (26.5800, 93.1700), (25.9000, 93.7300), (25.7500, 93.9500), (25.6751, 94.1086)],
    "c13": [(26.7271, 88.3953), (26.8800, 88.4700), (27.0500, 88.4300), (27.1700, 88.5200), (27.2400, 88.5500), (27.3389, 88.6065)]
}

FLEET = [
    {"user_id": "AS-01-EC-4412", "route_id": "c1", "speed_kmh": 48.0, "step": 0},
    {"user_id": "AR-02-B-1099", "route_id": "c3", "speed_kmh": 32.0, "step": 0},
    {"user_id": "MZ-01-T-7721", "route_id": "c7", "speed_kmh": 40.0, "step": 0},
    {"user_id": "MN-04-P-3342", "route_id": "c8", "speed_kmh": 35.0, "step": 0},
    {"user_id": "NL-07-A-8901", "route_id": "c9", "speed_kmh": 45.0, "step": 0},
    {"user_id": "SK-03-C-5561", "route_id": "c13", "speed_kmh": 38.0, "step": 0}
]

def calculate_heading(lat1, lon1, lat2, lon2):
    d_lon = math.radians(lon2 - lon1)
    y = math.sin(d_lon) * math.cos(math.radians(lat2))
    x = math.cos(math.radians(lat1)) * math.sin(math.radians(lat2)) - \
        math.sin(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.cos(d_lon)
    return round((math.degrees(math.atan2(y, x)) + 360) % 360, 1)

def run():
    print("[*] Setubandh AI - Fleet Telemetry Simulator Started")
    # Subdivide waypoints into granular road steps
    tracks = {}
    for rid, wps in ROUTES.items():
        pts = []
        for i in range(len(wps) - 1):
            p1, p2 = wps[i], wps[i+1]
            for s in range(25):
                t = s / 25
                pts.append((p1[0] + (p2[0] - p1[0]) * t, p1[1] + (p2[1] - p1[1]) * t))
        pts.append(wps[-1])
        tracks[rid] = pts

    while True:
        for v in FLEET:
            track = tracks[v["route_id"]]
            i = v["step"] % len(track)
            next_i = (i + 1) % len(track)
            curr_pt, next_pt = track[i], track[next_i]
            
            payload = {
                "user_id": v["user_id"],
                "latitude": round(curr_pt[0], 6),
                "longitude": round(curr_pt[1], 6),
                "speed_kmh": v["speed_kmh"],
                "heading": calculate_heading(curr_pt[0], curr_pt[1], next_pt[0], next_pt[1])
            }
            try:
                requests.post(API_URL, json=payload, timeout=2.0)
            except Exception:
                pass
            v["step"] = (v["step"] + 1) % len(track)
        
        print(f"[*] Telemetry synced for {len(FLEET)} vehicles to PostGIS.")
        time.sleep(2.5)

if __name__ == "__main__":
    run()