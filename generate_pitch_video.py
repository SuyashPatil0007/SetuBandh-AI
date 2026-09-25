import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.video.VideoClip import VideoClip
WIDTH, HEIGHT = 1920, 1080
FPS = 24
DURATION = 30.0

def make_text_image(draw_func):
    """Helper to create RGB frame using PIL."""
    img = Image.new("RGB", (WIDTH, HEIGHT), color=(7, 14, 23))
    draw = ImageDraw.Draw(img)
    draw_func(draw, img)
    return np.array(img)

def render_frame(t):
    """Generates frames based on the 30-second timeline."""
    
    # 0s - 6s: Problem Statement & Crisis Introduction
    if t < 6.0:
        def draw_scene_1(draw, img):
            # Background grid lines
            for y in range(0, HEIGHT, 80):
                draw.line([(0, y), (WIDTH, y)], fill=(15, 28, 44), width=1)
            for x in range(0, WIDTH, 80):
                draw.line([(x, 0), (x, HEIGHT)], fill=(15, 28, 44), width=1)

            # Glowing alert border
            draw.rectangle([40, 40, WIDTH-40, HEIGHT-40], outline=(239, 68, 68), width=3)
            
            # Text badges & title
            draw.text((120, 140), "SMART INDIA HACKATHON 2024", fill=(251, 191, 36))
            draw.text((120, 260), "PROJECT: SETUBANDH AI", fill=(45, 212, 191))
            draw.text((120, 380), "THE PROBLEM:", fill=(239, 68, 68))
            draw.text((120, 470), "Monsoon rain triggers frequent landslides across the North-Eastern Region.", fill=(240, 244, 248))
            draw.text((120, 550), "Trunk highways (NH37, NH13, NH29) lock down within minutes.", fill=(139, 162, 184))
            draw.text((120, 630), "Result: Critical medical, food, and fuel lifelines remain paralyzed.", fill=(139, 162, 184))

            # Metric card simulation
            draw.rectangle([120, 750, 600, 920], fill=(18, 33, 51), outline=(30, 50, 71), width=2)
            draw.text((160, 780), "512+ MONITORED HAZARD SITES", fill=(251, 191, 36))
            draw.text((160, 840), "Status: 14 Key Arterials Evaluated Runtime", fill=(240, 244, 248))

        return make_text_image(draw_scene_1)

    # 6s - 14s: Dual Interface Synchronization Architecture
    elif t < 14.0:
        def draw_scene_2(draw, img):
            draw.rectangle([40, 40, WIDTH-40, HEIGHT-40], outline=(45, 212, 191), width=2)
            draw.text((100, 80), "SYSTEM ARCHITECTURE: FULL-DUPLEX WEBSOCKET MESH", fill=(45, 212, 191))
            
            # Left Card: Admin Command Console
            draw.rectangle([100, 180, 900, 900], fill=(12, 24, 37), outline=(30, 50, 71), width=2)
            draw.text((140, 220), "ADMIN COMMAND TERMINAL (/admin)", fill=(251, 191, 36))
            draw.text((140, 300), "• Live Corridor Selection", fill=(240, 244, 248))
            draw.text((140, 360), "• Telemetry Rainfall Stress Slider", fill=(240, 244, 248))
            draw.text((140, 420), "• PostGIS 512 Regional Sites Layer", fill=(240, 244, 248))
            draw.text((140, 480), "• Real-Time Incident Ingestion Stream", fill=(240, 244, 248))

            # Progress simulated slider
            slide_progress = int(140 + min(600, (t - 6.0) * 80))
            draw.rectangle([140, 600, 740, 620], fill=(30, 50, 71))
            draw.rectangle([140, 600, slide_progress, 620], fill=(251, 191, 36))
            draw.text((140, 650), f"Current Rain Simulation: {int((t-6)*15)} mm", fill=(251, 191, 36))

            # Center Sync Bolt
            draw.text((930, 520), "<== WebSocket Mesh ==>", fill=(45, 212, 191))

            # Right Card: Driver Mobile Navigator
            draw.rectangle([1020, 180, 1820, 900], fill=(12, 24, 37), outline=(30, 50, 71), width=2)
            draw.text((1060, 220), "DRIVER NAVIGATOR (/driver)", fill=(45, 212, 191))
            draw.text((1060, 300), "• Zero-Touch Runtime Auto Updates", fill=(240, 244, 248))
            draw.text((1060, 360), "• Dynamic Visual Detour Cascading", fill=(240, 244, 248))
            draw.text((1060, 420), "• One-Tap Ground Hazard Reporting", fill=(240, 244, 248))
            draw.text((1060, 480), "• Multi-Lingual Indic Turn Advisories", fill=(240, 244, 248))

            # Driver live badge
            draw.rectangle([1060, 580, 1400, 650], fill=(18, 33, 51), outline=(45, 212, 191))
            draw.text((1090, 605), "STATE: LIVE SYNCHRONIZED", fill=(45, 212, 191))

        return make_text_image(draw_scene_2)

    # 14s - 23s: Tri-Tier Route Cascading Demonstration
    elif t < 23.0:
        def draw_scene_3(draw, img):
            draw.rectangle([40, 40, WIDTH-40, HEIGHT-40], outline=(251, 191, 36), width=2)
            draw.text((100, 80), "AI PREDICTION: TRI-TIER DYNAMIC EVASION IN RUNTIME", fill=(251, 191, 36))
            draw.text((100, 140), "Corridor: Shillong (Meghalaya) → Kohima (Nagaland)", fill=(240, 244, 248))

            # Phase 1: Direct Highway (Clear vs Blocked)
            if t < 17.0:
                # Direct Safe
                draw.rectangle([100, 240, 1820, 420], fill=(18, 33, 51), outline=(34, 197, 94), width=3)
                draw.text((140, 280), "TIER 1: DIRECT HIGHWAY TRUNK (NH37)", fill=(34, 197, 94))
                draw.text((140, 340), "Status: OPTIMAL (< 45mm Rain) | Distance: 371.5 km | ETA: 4.8 hrs", fill=(240, 244, 248))
            else:
                # Direct Blocked
                draw.rectangle([100, 240, 1820, 420], fill=(28, 18, 24), outline=(239, 68, 68), width=3)
                draw.text((140, 280), "TIER 1: DIRECT HIGHWAY TRUNK [BLOCKED BY AI HAZARD]", fill=(239, 68, 68))
                draw.text((140, 340), "Trigger 1 Active (> 45mm Rain) | Critical Landslide Risk Breach", fill=(239, 68, 68))

            # Phase 2: Secondary Valley Route
            if t >= 17.0 and t < 20.0:
                draw.rectangle([100, 460, 1820, 640], fill=(18, 33, 51), outline=(45, 212, 191), width=3)
                draw.text((140, 500), "TIER 2: VALLEY ARTERIAL BYPASS [ACTIVE DETOUR]", fill=(45, 212, 191))
                draw.text((140, 560), "Routing via Low-Gradient Valley Sector | Distance: 412 km | ETA: 5.6 hrs", fill=(240, 244, 248))
            elif t >= 20.0:
                draw.rectangle([100, 460, 1820, 640], fill=(28, 18, 24), outline=(239, 68, 68), width=3)
                draw.text((140, 500), "TIER 2: VALLEY ARTERIAL BYPASS [BLOCKED BY FLASH FLOOD]", fill=(239, 68, 68))
                draw.text((140, 560), "Trigger 2 Active (> 55mm Extreme Rain) | Riverbed Overflow", fill=(239, 68, 68))
            else:
                draw.rectangle([100, 460, 1820, 640], fill=(12, 24, 37), outline=(30, 50, 71), width=1)
                draw.text((140, 500), "TIER 2: VALLEY ARTERIAL BYPASS [STANDBY]", fill=(139, 162, 184))

            # Phase 3: High Ground Ridge Lifeline
            if t >= 20.0:
                draw.rectangle([100, 680, 1820, 860], fill=(30, 20, 45), outline=(168, 85, 247), width=3)
                draw.text((140, 720), "TIER 3: OUTER EMERGENCY HIGH-GROUND RIDGE LIFELINE [DISPATCHED]", fill=(168, 85, 247))
                draw.text((140, 780), "Evasion of low-lying floodplains | Zero-Break Supply Delivery Assured", fill=(240, 244, 248))
            else:
                draw.rectangle([100, 680, 1820, 860], fill=(12, 24, 37), outline=(30, 50, 71), width=1)
                draw.text((140, 720), "TIER 3: OUTER EMERGENCY HIGH-GROUND RIDGE LIFELINE [STANDBY]", fill=(139, 162, 184))

        return make_text_image(draw_scene_3)

    # 23s - 30s: Tech Stack & Final Impact
    else:
        def draw_scene_4(draw, img):
            draw.rectangle([40, 40, WIDTH-40, HEIGHT-40], outline=(45, 212, 191), width=3)
            draw.text((100, 140), "SETUBANDH AI: IMPACT & CORE STACK", fill=(45, 212, 191))
            
            # Stack elements
            stack = [
                "FastAPI Asynchronous Web Engine",
                "PostGIS / PostgreSQL Spatial Graph Database",
                "Random Forest Machine Learning Hazard Model",
                "Bidirectional WebSocket Mesh Synchronizer",
                "Digital India Bhashini Indic Localization Engine"
            ]
            
            y_pos = 260
            for item in stack:
                draw.rectangle([100, y_pos, 900, y_pos + 60], fill=(18, 33, 51), outline=(30, 50, 71), width=1)
                draw.text((130, y_pos + 15), f"✔  {item}", fill=(240, 244, 248))
                y_pos += 80

            # Impact summary
            draw.rectangle([980, 260, 1820, 780], fill=(12, 24, 37), outline=(251, 191, 36), width=2)
            draw.text((1030, 320), "REAL-WORLD DEPLOYMENT READY", fill=(251, 191, 36))
            draw.text((1030, 410), "• Eliminates stranded convoy gridlocks in NE region", fill=(240, 244, 248))
            draw.text((1030, 480), "• Reduces disaster logistics detour latency by 70%", fill=(240, 244, 248))
            draw.text((1030, 550), "• 100% sovereign Indic language voice & text support", fill=(240, 244, 248))
            draw.text((1030, 620), "• Ready for integration with MDoNER & State DMAs", fill=(240, 244, 248))

            draw.text((100, 920), "SETUBANDH AI — UNBROKEN SUPPLY CHAINS WHEN DISASTER STRIKES", fill=(45, 212, 191))

        return make_text_image(draw_scene_4)

# Build & render video
print("[*] Generating 30-second SIH pitch video frames...")
clip = VideoClip(render_frame, duration=DURATION)
clip.write_videofile("setubandh_sih_pitch.mp4", fps=FPS, codec="libx264")
print("[+] Video generated successfully: setubandh_sih_pitch.mp4")