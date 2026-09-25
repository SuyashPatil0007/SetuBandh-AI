from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
from database import Base

# ---------------------------------------------------------
# 1. LIVE USER GPS TELEMETRY
# ---------------------------------------------------------
class UserLocationPing(Base):
    __tablename__ = "user_location_pings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), index=True, nullable=False)
    speed_kmh = Column(Float, nullable=True)
    heading = Column(Float, nullable=True)
    # Point with standard GPS coordinates (WGS 84, SRID 4326)
    location = Column(Geometry(geometry_type="POINT", srid=4326), nullable=False)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


# ---------------------------------------------------------
# 2. ROAD NETWORK SEGMENTS (NORTHEAST MAP)
# ---------------------------------------------------------
class RoadSegment(Base):
    __tablename__ = "road_segments"

    id = Column(Integer, primary_key=True, index=True)
    osm_id = Column(String(50), unique=True, nullable=True)
    name = Column(String(255), nullable=True)           # e.g., "NH-29", "Guwahati-Shillong corridor"
    state = Column(String(100), nullable=True)          # Assam, Meghalaya, etc.
    surface_type = Column(String(50), nullable=True)     # Paved, Unpaved, Gravel
    geometry = Column(Geometry(geometry_type="LINESTRING", srid=4326), nullable=False)


# ---------------------------------------------------------
# 3. DRIVER / CROWDSOURCED INCIDENT REPORTS
# ---------------------------------------------------------
class CrowdIncidentReport(Base):
    __tablename__ = "incident_reports"

    id = Column(Integer, primary_key=True, index=True)
    reporter_id = Column(String(100), nullable=False)
    incident_type = Column(String(100), nullable=False)  # "LANDSLIDE", "FLOODING", "ACCIDENT", "ROAD_BLOCKED"
    severity = Column(String(20), default="MEDIUM")      # LOW, MEDIUM, CRITICAL
    description = Column(Text, nullable=True)
    location = Column(Geometry(geometry_type="POINT", srid=4326), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


# ---------------------------------------------------------
# 4. HIGHWAY SURVEILLANCE & AI CAMERAS
# ---------------------------------------------------------
class HighwayCamera(Base):
    __tablename__ = "highway_cameras"

    id = Column(Integer, primary_key=True, index=True)
    highway_code = Column(String(50), index=True, nullable=True)  # e.g., "NH-37"
    rtsp_stream_url = Column(String(500), nullable=True)
    latest_ai_flag = Column(JSON, nullable=True)                  # e.g., {"water_logging": true, "debris": false}
    location = Column(Geometry(geometry_type="POINT", srid=4326), nullable=False)
    last_ping_at = Column(DateTime(timezone=True), onupdate=func.now())


# ---------------------------------------------------------
# 5. HISTORICAL CALAMITY-PRONE ZONES
# ---------------------------------------------------------
class HazardZone(Base):
    __tablename__ = "hazard_zones"

    id = Column(Integer, primary_key=True, index=True)
    zone_name = Column(String(255), nullable=False)               # e.g., "Dima Hasao Landslide Corridor"
    hazard_type = Column(String(100), nullable=False)             # "LANDSLIDE", "FLASH_FLOOD", "SOIL_EROSION"
    risk_level = Column(String(50), default="HIGH")               # MODERATE, HIGH, EXTREME
    historical_event_count = Column(Integer, default=1)
    boundary = Column(Geometry(geometry_type="MULTIPOLYGON", srid=4326), nullable=False)


# ---------------------------------------------------------
# 6. WEATHER INTEGRATION / CHECKPOINT SNAPSHOTS
# ---------------------------------------------------------
class WeatherCheckpoint(Base):
    __tablename__ = "weather_checkpoints"

    id = Column(Integer, primary_key=True, index=True)
    station_or_location_name = Column(String(255), nullable=True) # e.g., "Cherrapunji Station"
    temperature_celsius = Column(Float, nullable=True)
    rainfall_mm_per_hour = Column(Float, default=0.0)             # Key indicator for landslide risk
    wind_speed_kmh = Column(Float, nullable=True)
    visibility_meters = Column(Float, nullable=True)
    weather_condition = Column(String(100), nullable=True)         # "HEAVY_RAIN", "FOG", "CLEAR"
    raw_payload = Column(JSON, nullable=True)
    location = Column(Geometry(geometry_type="POINT", srid=4326), nullable=False)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)