import os
import glob
import json
import pandas as pd
from shapely.geometry import Point, mapping

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HAZARD_DIR = os.path.join(BASE_DIR, "data", "Hazard_Zone")

# 0.003 degrees ≈ 300 to 350 meters danger radius
BUFFER_DEGREE = 0.003

def batch_convert_csv_to_geojson():
    csv_files = glob.glob(os.path.join(HAZARD_DIR, "*.csv"))

    if not csv_files:
        print(f"[!] No CSV files found in: {HAZARD_DIR}")
        return

    print(f"[*] Found {len(csv_files)} CSV dataset(s) to process.\n")

    for file_path in csv_files:
        file_name = os.path.basename(file_path)
        base_name = os.path.splitext(file_name)[0]
        output_file = os.path.join(HAZARD_DIR, f"{base_name.lower()}.geojson")

        try:
            df = pd.read_csv(file_path)
            
            # Normalize column names to lowercase for robust lookup
            col_map = {col.lower().strip(): col for col in df.columns}
            
            lat_col = col_map.get("latitude") or col_map.get("lat")
            lon_col = col_map.get("longitude") or col_map.get("long") or col_map.get("lon")

            if not lat_col or not lon_col:
                print(f"[-] Skipped {file_name}: Missing latitude/longitude columns.")
                continue

            features = []
            for _, row in df.iterrows():
                try:
                    lat = float(row[lat_col])
                    lon = float(row[lon_col])
                except (ValueError, TypeError):
                    continue

                if pd.isna(lat) or pd.isna(lon):
                    continue

                # Buffer point into a circular polygon hazard perimeter
                pt = Point(lon, lat)
                buffered_geom = pt.buffer(BUFFER_DEGREE)

                # Safe fallback property mappings
                state_val = row.get(col_map.get("state", ""), "Northeast Region")
                district_val = row.get(col_map.get("district", ""), "Unknown")
                name_val = row.get(col_map.get("name", ""), f"Landslide Zone ({district_val})")
                locality_val = row.get(col_map.get("locality", ""), "")
                landslide_id = str(row.get(col_map.get("landslide_id", ""), "UNKNOWN_ID"))

                features.append({
                    "type": "Feature",
                    "properties": {
                        "landslide_id": landslide_id,
                        "zone_name": f"{name_val} - {locality_val}".strip(" -"),
                        "state": str(state_val),
                        "district": str(district_val),
                        "hazard_type": "LANDSLIDE",
                        "risk_level": "HIGH",
                        "historical_event_count": 1
                    },
                    "geometry": mapping(buffered_geom)
                })

            geojson_doc = {
                "type": "FeatureCollection",
                "name": base_name,
                "features": features
            }

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(geojson_doc, f, indent=2)

            print(f"[+] Converted {file_name} -> {os.path.basename(output_file)} ({len(features)} zones)")

        except Exception as err:
            print(f"[!] Error processing {file_name}: {err}")

    print("\n[SUCCESS] Batch conversion complete.")

if __name__ == "__main__":
    batch_convert_csv_to_geojson()