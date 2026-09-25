# 🌉 Setubandh AI
> **Disaster-Resilient Lifeline Logistics & Intelligent Multi-Tier Evasion Routing for North-East India**  
> *Smart India Hackathon (SIH)*

---

## 📌 Executive Summary
During monsoon seasons across the North-Eastern Region (NER) of India, sudden landslides, rockfalls, and flash floods sever vital national highways (NH37, NH13, NH29) within minutes, cutting off essential relief supply chains—including blood bank supplies, dialysis medication, petroleum, and essential grains.

**Setubandh AI** is a real-time roadway intelligence and lifeline routing platform that dynamically models geological and meteorological hazards. By combining predictive machine learning, PostGIS spatial analysis, and a full-duplex WebSocket mesh, it calculates safe, cascading multi-tier detours and synchronizes them instantly across dispatchers and field drivers before convoys reach hazardous choke points.

---

## ⚡ Key Technical Innovations

* **Predictive AI Risk Modeling:** A trained **Random Forest Regressor** (`road_risk_rf.joblib`) scores roadway vulnerability ($0\text{–}100$ scale) using precipitation telemetry and historical landslide frequencies.
* **Cascading Tri-Tier Routing Engine:** Automatically triggers safe route transitions using Open Source Routing Machine (OSRM) and PostGIS:
  * **Tier 1 (Direct Trunk Highway):** Primary transit corridor, active under clear conditions ($<45\text{ mm}$ rainfall).
  * **Tier 2 (Secondary Valley Bypass):** Automatically deployed when primary route risk breaches $\ge 45\text{ mm}$ rainfall or a risk score of $45/100$.
  * **Tier 3 (Outer High-Ground Ridge Lifeline):** Automatically engaged during extreme events ($\ge 55\text{ mm}$ rainfall) to guide convoys away from low-lying floodplains.
* **Full-Duplex WebSocket Mesh:** Bi-directional synchronization connects the Central Command Console (`ner2.html`) and Driver Mobile Navigator (`nertrial.html`) into a single source of truth—updating routes in runtime without manual button clicks or page reloads.
* **1-Tap Crowdsourced Telemetry:** Field drivers report active mudslips, road washouts, or flash floods with a single tap, dropping geo-referenced hazard pins on dispatch consoles and initiating automated telephony alerts (call/SMS).
* **Indic Multi-Language Localization:** Native translation support for regional Indian languages—**Assamese (অসমীয়া), Bengali (বাংলা), Hindi (हिन्दी), and English**—for dynamic route advisories and driver interfaces.

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend & APIs** | FastAPI, Python 3, Uvicorn, Asynchronous WebSockets |
| **Spatial Database** | PostgreSQL, PostGIS, GeoAlchemy2, SQLAlchemy |
| **Routing & AI** | OSRM Graph Engine, Scikit-Learn Random Forest Regressor |
| **Frontend Interfaces** | Leaflet.js, High-Resolution Satellite GIS Layers, HTML5 Geolocation |
| **Telemetry & Services** | Open-Meteo Satellite Precipitation API, Indic Translation Pipeline, Telephony Dispatch |

---

## 📁 Repository Structure

```text
SetuBandh-AI/
├── data/Hazard_Zone/       # GSI landslide inventories & regional GeoJSON/CSV datasets
├── models.py               # SQLAlchemy database models (incidents, pings, hazard zones)
├── schemas.py              # Pydantic schemas for data validation
├── database.py             # PostgreSQL / PostGIS engine and session connection
├── ai_engine.py            # Random Forest risk inference engine
├── road_risk_rf.joblib     # Pre-trained scikit-learn hazard regression model
├── telephony_services.py   # Driver dispatch, voice calls & SMS alerts
├── translation_services.py # Indic localization pipeline (Assamese, Bengali, Hindi)
├── traffic_services.py     # Real-time traffic flow telemetry integrations
├── ner2.html               # Central Command Monitoring & Dispatch Console
├── nertrial.html           # Driver Mobile Navigation Interface
├── main.py                 # FastAPI application & WebSocket state hub
└── requirements.txt        # Python package dependencies