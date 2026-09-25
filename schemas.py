from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# =========================================================
# 1. LIVE USER GPS TELEMETRY
# =========================================================
class UserLocationPingCreate(BaseModel):
    user_id: str = Field(..., description="Unique user or device identifier")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="WGS84 Latitude (-90 to 90)")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="WGS84 Longitude (-180 to 180)")
    speed_kmh: Optional[float] = Field(default=None, ge=0.0, description="Current speed in km/h")
    heading: Optional[float] = Field(default=None, ge=0.0, le=360.0, description="Compass bearing (0-360 degrees)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "usr_northeast_8819",
                "latitude": 26.1445,
                "longitude": 91.7362,
                "speed_kmh": 48.5,
                "heading": 125.0
            }
        }
    }


class UserLocationPingResponse(BaseModel):
    id: int
    user_id: str
    latitude: float
    longitude: float
    speed_kmh: Optional[float] = None
    heading: Optional[float] = None
    recorded_at: datetime

    model_config = {"from_attributes": True}


# =========================================================
# 2. ROAD NETWORK SEGMENTS (NORTHEAST MAP)
# =========================================================
class RoadSegmentCreate(BaseModel):
    osm_id: Optional[str] = Field(default=None, description="OpenStreetMap way identifier")
    name: Optional[str] = Field(default=None, description="Highway code or route name, e.g., 'NH-29'")
    state: Optional[str] = Field(default=None, description="Northeast State name, e.g., 'Assam'")
    surface_type: Optional[str] = Field(default="Paved", description="Paved, Unpaved, Gravel, etc.")
    # Line coordinates as a sequence of [longitude, latitude] pairs (standard GeoJSON format)
    coordinates: List[List[float]] = Field(
        ...,
        min_length=2,
        description="LineString coordinates: list of [lon, lat] pairs"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "osm_id": "way_4920194",
                "name": "NH-29 Dimapur-Kohima Corridor",
                "state": "Nagaland",
                "surface_type": "Paved",
                "coordinates": [
                    [93.7259, 25.9068],
                    [93.8500, 25.8000],
                    [94.1086, 25.6751]
                ]
            }
        }
    }


class RoadSegmentResponse(BaseModel):
    id: int
    osm_id: Optional[str] = None
    name: Optional[str] = None
    state: Optional[str] = None
    surface_type: Optional[str] = None
    coordinates: List[List[float]]

    model_config = {"from_attributes": True}


# =========================================================
# 3. DRIVER / CROWDSOURCED INCIDENT REPORTS
# =========================================================
class CrowdIncidentReportCreate(BaseModel):
    reporter_id: str = Field(..., description="Reporting driver/user identifier")
    incident_type: str = Field(..., description="LANDSLIDE, FLOODING, ACCIDENT, or ROAD_BLOCKED")
    severity: str = Field(default="MEDIUM", description="Severity level: LOW, MEDIUM, or CRITICAL")
    description: Optional[str] = Field(default=None, description="Additional context or notes")
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)

    model_config = {
        "json_schema_extra": {
            "example": {
                "reporter_id": "driver_dima_hasao_04",
                "incident_type": "LANDSLIDE",
                "severity": "CRITICAL",
                "description": "Mud and boulders blocking both lanes near Jatinga",
                "latitude": 25.1204,
                "longitude": 93.0381
            }
        }
    }


class CrowdIncidentReportResponse(BaseModel):
    id: int
    reporter_id: str
    incident_type: str
    severity: str
    description: Optional[str] = None
    latitude: float
    longitude: float
    created_at: datetime

    model_config = {"from_attributes": True}


# =========================================================
# 4. HIGHWAY SURVEILLANCE & AI CAMERAS
# =========================================================
class HighwayCameraCreate(BaseModel):
    highway_code: Optional[str] = Field(default=None, description="Highway code, e.g., 'NH-37'")
    rtsp_stream_url: Optional[str] = Field(default=None, description="RTSP / HLS streaming URL")
    latest_ai_flag: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Structured JSON flag from vision pipeline"
    )
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)

    model_config = {
        "json_schema_extra": {
            "example": {
                "highway_code": "NH-37",
                "rtsp_stream_url": "rtsp://camera.assamhighways.gov.in/nh37/cam_01",
                "latest_ai_flag": {
                    "water_logging": True,
                    "debris_detected": False,
                    "visibility_score": 0.85
                },
                "latitude": 26.1823,
                "longitude": 91.7618
            }
        }
    }


class HighwayCameraResponse(BaseModel):
    id: int
    highway_code: Optional[str] = None
    rtsp_stream_url: Optional[str] = None
    latest_ai_flag: Optional[Dict[str, Any]] = None
    latitude: float
    longitude: float
    last_ping_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# =========================================================
# 5. HISTORICAL CALAMITY-PRONE ZONES
# =========================================================
class HazardZoneCreate(BaseModel):
    zone_name: str = Field(..., description="Vulnerable area or corridor name")
    hazard_type: str = Field(..., description="LANDSLIDE, FLASH_FLOOD, or SOIL_EROSION")
    risk_level: str = Field(default="HIGH", description="MODERATE, HIGH, or EXTREME")
    historical_event_count: int = Field(default=1, ge=1)
    # GeoJSON MultiPolygon coordinates format: List of polygons -> rings -> [lon, lat]
    polygon_coordinates: List[List[List[List[float]]]] = Field(
        ...,
        description="MultiPolygon coordinates matching GeoJSON spec"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "zone_name": "Dima Hasao Landslide Corridor",
                "hazard_type": "LANDSLIDE",
                "risk_level": "EXTREME",
                "historical_event_count": 14,
                "polygon_coordinates": [
                    [
                        [
                            [92.9500, 25.1000],
                            [93.1500, 25.1000],
                            [93.1500, 25.2500],
                            [92.9500, 25.2500],
                            [92.9500, 25.1000]
                        ]
                    ]
                ]
            }
        }
    }


class HazardZoneResponse(BaseModel):
    id: int
    zone_name: str
    hazard_type: str
    risk_level: str
    historical_event_count: int
    polygon_coordinates: List[List[List[List[float]]]]

    model_config = {"from_attributes": True}


# =========================================================
# 6. WEATHER INTEGRATION / CHECKPOINT SNAPSHOTS
# =========================================================
class WeatherCheckpointCreate(BaseModel):
    station_or_location_name: Optional[str] = Field(default=None, description="Station or checkpoint name")
    temperature_celsius: Optional[float] = None
    rainfall_mm_per_hour: float = Field(default=0.0, ge=0.0, description="Hourly rainfall rate in mm")
    wind_speed_kmh: Optional[float] = Field(default=None, ge=0.0)
    visibility_meters: Optional[float] = Field(default=None, ge=0.0)
    weather_condition: Optional[str] = Field(default=None, description="HEAVY_RAIN, FOG, CLEAR, etc.")
    raw_payload: Optional[Dict[str, Any]] = None
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)

    model_config = {
        "json_schema_extra": {
            "example": {
                "station_or_location_name": "Cherrapunji Weather Outpost",
                "temperature_celsius": 18.2,
                "rainfall_mm_per_hour": 45.0,
                "wind_speed_kmh": 22.4,
                "visibility_meters": 150.0,
                "weather_condition": "HEAVY_RAIN",
                "latitude": 25.2702,
                "longitude": 91.7323
            }
        }
    }


class WeatherCheckpointResponse(BaseModel):
    id: int
    station_or_location_name: Optional[str] = None
    temperature_celsius: Optional[float] = None
    rainfall_mm_per_hour: float
    wind_speed_kmh: Optional[float] = None
    visibility_meters: Optional[float] = None
    weather_condition: Optional[str] = None
    latitude: float
    longitude: float
    recorded_at: datetime

    model_config = {"from_attributes": True}