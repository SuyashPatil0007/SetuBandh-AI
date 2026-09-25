import httpx
from typing import Dict, Tuple

TOMTOM_API_KEY = "YOUR_TOMTOM_API_KEY"

async def fetch_corridor_traffic_flow(lat: float, lon: float) -> float:
    """
    Returns a congestion multiplier (1.0 = clear, 2.0 = 50% speed drop, 4.0+ = gridlock).
    """
    url = (
        f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"
        f"?point={lat},{lon}&key={TOMTOM_API_KEY}&unit=KMPH"
    )
    try:
        async with httpx.AsyncClient(timeout=1.5) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json().get("flowSegmentData", {})
                current_speed = data.get("currentSpeed", 40)
                free_flow_speed = data.get("freeFlowSpeed", 40)
                
                if current_speed <= 5:
                    return 5.0  # Heavy gridlock / breakdown
                return round(max(1.0, free_flow_speed / current_speed), 2)
    except Exception:
        pass
    return 1.0  # Default to normal flow if API is unreachable