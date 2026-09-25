import time

ALERT_COOLDOWN_CACHE = {}
COOLDOWN_SECONDS = 180

def can_dispatch(phone: str) -> bool:
    now = time.time()
    last_sent = ALERT_COOLDOWN_CACHE.get(phone, 0)
    if now - last_sent > COOLDOWN_SECONDS:
        ALERT_COOLDOWN_CACHE[phone] = now
        return True
    return False

def send_driver_sms(to_phone: str, vehicle_id: str, hazard_type: str, corridor_name: str, detour_info: str):
    """Simulates 2G SMS dispatch for remote hill corridors."""
    if not can_dispatch(to_phone):
        print(f"[*] Telephony Cooldown active for {to_phone}. Skipping repeated SMS.")
        return {"status": "COOLDOWN"}

    msg_lines = [
        "[SETUBANDH AI DISPATCH]",
        f"Vehicle: {vehicle_id}",
        f"Hazard: {hazard_type} reported ahead on {corridor_name}!",
        f"ACTION REQUIRED: Immediate bypass triggered via {detour_info}.",
        "Do NOT enter primary corridor. Drive safe."
    ]
    message_body = "\n".join(msg_lines)

    print("\n" + "=" * 65)
    print(f"📱 [OUTBOUND SMS DISPATCHED] -> {to_phone}")
    print(f"Fleet Vehicle Target : {vehicle_id}")
    print(f"Cellular Protocol    : GSM 03.40 (2G SMS Fallback)")
    print("SMS Payload Content  :\n" + message_body)
    print("=" * 65 + "\n")

    return {"status": "SENT", "sid": f"SIM_SMS_{int(time.time())}"}

def dispatch_driver_call(to_phone: str, vehicle_id: str, hazard_type: str, detour_info: str):
    """Simulates automated Outbound Voice Call (IVR/TTS) to driver phone."""
    print("\n" + "#" * 65)
    print(f"📞 [OUTBOUND VOICE CALL DIALING] -> {to_phone}")
    print(f"Fleet Vehicle Target    : {vehicle_id}")
    print(f"Voice Audio Synthesizer : AWS Polly.Aditi (en-IN Accented)")
    print("Spoken Voice Transcript :")
    print(f'   "Attention driver of vehicle {vehicle_id}. This is Setubandh Emergency Control.')
    print(f'    The route ahead is obstructed due to a {hazard_type}.')
    print(f'    Please divert immediately onto {detour_info}.')
    print('    Do not proceed on the primary highway. Drive safely."')
    print("#" * 65 + "\n")

    return {"status": "CALLING", "sid": f"SIM_CALL_{int(time.time())}"}