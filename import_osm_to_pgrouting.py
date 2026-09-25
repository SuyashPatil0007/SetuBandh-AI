import sys
import numpy as np
import geopandas as gpd
from sqlalchemy import create_engine, text

DB_URL = "postgresql://postgres:suyash123@localhost:5432/setubandh_db"
engine = create_engine(DB_URL)

PBF_FILE = "north-eastern-zone-latest.osm.pbf"
print(f"[*] Reading lines layer from {PBF_FILE}...")

try:
    roads = gpd.read_file(
        PBF_FILE,
        layer="lines",
        engine="pyogrio",
        columns=["osm_id", "name", "highway", "geometry"]
    )
except Exception as e:
    print(f"[-] Error opening PBF file: {e}")
    sys.exit(1)

drivable = [
    "motorway", "motorway_link", "trunk", "trunk_link",
    "primary", "primary_link", "secondary", "secondary_link",
    "tertiary", "tertiary_link", "unclassified", "residential"
]
roads = roads[roads["highway"].isin(drivable)].copy()
roads = roads[roads.geometry.geom_type == "LineString"].copy()

# Ensure standard WGS84 projection
if roads.crs is None:
    roads.set_crs(epsg=4326, inplace=True)
else:
    roads = roads.to_crs(epsg=4326)

# Spherical length calculation in meters
roads_proj = roads.to_crs(epsg=3857)
roads["length_m"] = roads_proj.geometry.length

# Round node coordinate keys to 5 decimal places (~1.1m) to fix disjointed intersections
print("[*] Building connected graph topology vertices...")
def snap_coord(coord):
    return (round(coord[0], 5), round(coord[1], 5))

start_coords = roads.geometry.apply(lambda geom: snap_coord(geom.coords[0]))
end_coords = roads.geometry.apply(lambda geom: snap_coord(geom.coords[-1]))

unique_points = list(set(start_coords.tolist() + end_coords.tolist()))
point_to_id = {pt: idx + 1 for idx, pt in enumerate(unique_points)}

roads["source"] = start_coords.map(point_to_id)
roads["target"] = end_coords.map(point_to_id)
roads["gid"] = np.arange(1, len(roads) + 1)
roads = roads.rename_geometry("the_geom")

print("[*] Ingesting 'ways' table into PostGIS...")
with engine.begin() as conn:
    conn.execute(text("DROP TABLE IF EXISTS ways CASCADE;"))

roads[["gid", "osm_id", "name", "highway", "length_m", "source", "target", "the_geom"]].to_postgis(
    "ways", engine, if_exists="replace", index=False
)

print("[*] Creating spatial and topological indexes...")
with engine.begin() as conn:
    conn.execute(text("ALTER TABLE ways ADD PRIMARY KEY (gid);"))
    conn.execute(text("CREATE INDEX ways_geom_idx ON ways USING GIST (the_geom);"))
    conn.execute(text("CREATE INDEX ways_source_idx ON ways (source);"))
    conn.execute(text("CREATE INDEX ways_target_idx ON ways (target);"))
    conn.execute(text("CREATE INDEX ways_highway_idx ON ways (highway);"))

print("[SUCCESS] Topology successfully generated.")