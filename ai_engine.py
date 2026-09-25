import os
import joblib

MODEL_PATH = os.path.join(os.path.dirname(__file__), "road_risk_rf.joblib")

class RoadRiskAI:
    def __init__(self):
        if os.path.exists(MODEL_PATH):
            self.model = joblib.load(MODEL_PATH)
            print("[+] Setubandh AI: Random Forest model loaded.")
        else:
            self.model = None
            print("[!] Warning: 'road_risk_rf.joblib' not found. Using fallback logic.")

    def predict_risk(self, rainfall_mm: float, road_tier: int, landslide_history: int) -> float:
        """
        Predicts continuous 0-100 road risk score using the trained Random Forest.
        road_tier: 1 = Highway/Trunk, 2 = Secondary, 3 = Rural/Village Cut
        """
        if self.model is not None:
            features = [[float(rainfall_mm), int(road_tier), int(landslide_history)]]
            pred = float(self.model.predict(features)[0])
            return round(max(0.0, min(100.0, pred)), 2)

        # Fallback formula if model file is missing
        fallback = (rainfall_mm * 0.35) + (road_tier * 8.0) + (landslide_history * 4.0) + 15.0
        return round(max(0.0, min(100.0, fallback)), 2)

    def select_best_route(self, candidate_routes: list) -> dict:
        """
        Ranks candidate routes using composite scoring: 70% risk / 30% distance.
        Lowest composite score indicates the safest and most optimal route.
        """
        if not candidate_routes:
            return None
        if len(candidate_routes) == 1:
            candidate_routes[0]["composite_score"] = 0.0
            return candidate_routes[0]

        risks = [r["risk_score"] for r in candidate_routes]
        dists = [r["distance_km"] for r in candidate_routes]

        r_min, r_max = min(risks), max(risks)
        d_min, d_max = min(dists), max(dists)

        for r in candidate_routes:
            norm_r = (r["risk_score"] - r_min) / (r_max - r_min) if (r_max - r_min) > 0 else 0.0
            norm_d = (r["distance_km"] - d_min) / (d_max - d_min) if (d_max - d_min) > 0 else 0.0
            r["composite_score"] = round((0.7 * norm_r) + (0.3 * norm_d), 3)

        candidate_routes.sort(key=lambda x: x["composite_score"])
        return candidate_routes[0]

ai_hazard_predictor = RoadRiskAI()