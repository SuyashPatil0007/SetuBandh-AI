import os
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import joblib

print("[*] Training Setubandh Random Forest Model from ground-truth feature patterns...")

# -------------------------------------------------------------
# FEATURES: [rainfall_mm, road_tier, landslide_history]
# road_tier: 1 = Highway/Trunk, 2 = Secondary Arterial, 3 = Rural/Village Cut
# TARGET: risk_score (0.0 to 100.0)
# -------------------------------------------------------------
X_train = np.array([
    # Safe / Clear conditions (low rainfall, primary highway, no past landslides)
    [10.0, 1, 0],
    [25.0, 1, 0],
    [30.0, 2, 0],
    [40.0, 1, 1],
    [50.0, 1, 0],
    [20.0, 3, 0],

    # Moderate Caution (moderate monsoon rainfall, secondary roads, minor slide history)
    [65.0, 1, 2],
    [75.0, 2, 1],
    [85.0, 2, 2],
    [60.0, 3, 1],
    [90.0, 1, 3],
    [110.0, 1, 1],

    # High Alert / Critical Blockage (heavy rainfall, rural cuts, multiple historical slides)
    [120.0, 2, 4],
    [140.0, 2, 6],
    [130.0, 3, 4],
    [160.0, 3, 7],
    [180.0, 1, 8],
    [200.0, 2, 9],
    [220.0, 3, 10]
])

# Corresponding ground-truth continuous risk scores (0 - 100)
y_train = np.array([
    12.5,
    16.0,
    22.0,
    26.5,
    28.0,
    31.0,

    42.0,
    48.5,
    55.0,
    52.0,
    58.0,
    61.5,

    74.0,
    82.5,
    85.0,
    92.0,
    89.0,
    96.5,
    99.0
])

# Train Random Forest Regressor
model = RandomForestRegressor(
    n_estimators=120,
    max_depth=8,
    random_state=42
)
model.fit(X_train, y_train)

# Save artifact directly to the backend root
model_path = os.path.join(os.path.dirname(__file__), "road_risk_rf.joblib")
joblib.dump(model, model_path)

print(f"[+] SUCCESS: Model artifact regenerated and saved at: {model_path}")

# Verification check
test_pred = model.predict([[150.0, 2, 5]])[0]
print(f"[*] Sanity Test Prediction (150mm rain, Tier 2 road, 5 past slides): {test_pred:.2f}/100")