import os
import json
import glob
from shapely.geometry import shape, MultiPolygon, Polygon
from geoalchemy2.shape import from_shape
from sqlalchemy import text
from database import SessionLocal
import models

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data", "Hazard_Zone")


def load_hazard_zones():
    db = SessionLocal()
    
    # 1. Grab all GeoJSON files in data/Hazard_Zone/
    geojson_files = sorted(
        glob.glob(os.path.join(DATA_DIR, "*.geojson"))
        + glob.glob(os.path.join(DATA_DIR, "*.json"))
    )

    if not geojson_files:
        print(f"[!] No GeoJSON files found in: {DATA_DIR}")
        print("    Run 'python convert_gsi_to_geojson.py' first.")
        db.close()
        return

    print(f"[*] Found {len(geojson_files)} GeoJSON dataset(s) to ingest.")

    # 2. Reset table to avoid duplicate rows across multiple runs
    choice = input("\nClear existing rows in 'hazard_zones' table before loading? (y/n): ").strip().lower()
    if choice == "y":
        db.execute(text("TRUNCATE TABLE hazard_zones RESTART IDENTITY CASCADE;"))
        db.commit()
        print("[*] Cleared existing table data.\n")

    total_inserted = 0

    try:
        for file_path in geojson_files:
            file_name = os.path.basename(file_path)
            state_slug = os.path.splitext(file_name)[0].replace("_", " ").title()

            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            features = data.get("features", [])
            state_inserted = 0

            for feature in features:
                raw_props = feature.get("properties", {})
                geom_data = feature.get("geometry")

                if not geom_data:
                    continue

                # Lowercase dictionary keys to avoid key mismatches
                props = {k.lower().strip(): v for k, v in raw_props.items() if v is not None}

                # Resolve Zone Name dynamically
                zone_name = (
                    props.get("zone_name")
                    or props.get("name")
                    or props.get("locality")
                    or props.get("landslide_id")
                    or f"{state_slug} Landslide Corridor"
                )

                # Resolve Hazard Type & Risk Level
                hazard_type = str(props.get("hazard_type", "LANDSLIDE")).upper()
                risk_level = str(props.get("risk_level", "HIGH")).upper()

                # Resolve Event Count
                try:
                    event_count = int(
                        props.get("historical_event_count")
                        or props.get("event_count")
                        or 1
                    )
                except (ValueError, TypeError):
                    event_count = 1

                # Convert geometry to Shapely MultiPolygon
                shapely_geom = shape(geom_data)
                if isinstance(shapely_geom, Polygon):
                    shapely_geom = MultiPolygon([shapely_geom])
                elif not isinstance(shapely_geom, MultiPolygon):
                    continue

                # Wrap with PostGIS SRID 4326
                postgis_geom = from_shape(shapely_geom, srid=4326)

                zone_entry = models.HazardZone(
                    zone_name=str(zone_name).strip(),
                    hazard_type=hazard_type,
                    risk_level=risk_level,
                    historical_event_count=event_count,
                    boundary=postgis_geom,
                )

                db.add(zone_entry)
                state_inserted += 1

            db.commit()
            print(f" [+] {file_name:<35} -> {state_inserted:>4} zones inserted")
            total_inserted += state_inserted

        print(f"\n[SUCCESS] Ingested all datasets. Total zones saved in PostGIS: {total_inserted}")

    except Exception as exc:
        db.rollback()
        print(f"[!] Database error during ingestion: {exc}")
    finally:
        db.close()


if __name__ == "__main__":
    load_hazard_zones()