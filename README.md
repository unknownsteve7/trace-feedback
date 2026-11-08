# TRACE Passenger Feedback Service (FastAPI)
**QR-Based Citizen Grievance & Passenger Experience Ingestion Service**

This component powers **Pillar 3 (Fact_Complaints)** of the TRACE transit platform. Passengers scan a vehicle QR code sticker, fill out a lightweight mobile form with auto-filled vehicle/route parameters, and their reports are ingested into the analytics pipeline to correlate with measured delay and bus bunching.

---

## 🏛️ Architecture & Data Flow

```
[QR Sticker on Bus] 
        ↓  (Scan carries ?r=<route_id>&v=<vehicle_id>)
[Mobile Web Form (GET /feedback)] 
        ↓  (Passenger submits ratings & remarks)
[FastAPI Ingestion Engine (POST /feedback)] 
        ↓  (Honeypot check, Salted Device Hash, Sliding-Window Rate Limit)
[Append-Only Feedback Database] 
        ↓  (Admin API Pull GET /admin/export)
[TRACE Medallion Lakehouse: Bronze → Silver → Gold Fact_Complaints]
```

---

## 📂 Folder Layout

```text
trace-feedback/
├── app/
│   ├── main.py              # Application lifecycle, CORS, router mounting
│   ├── config.py            # Pydantic Settings & environment variables
│   ├── database.py          # Async SQLAlchemy engine & session factory
│   ├── models.py            # Feedback table schema definition
│   ├── schemas.py           # Pydantic validation schemas & honeypots
│   ├── routers/
│   │   ├── feedback.py      # GET /feedback (serves form), POST /feedback
│   │   ├── meta.py          # GET /health, GET /categories
│   │   └── admin.py         # GET /admin/export (API-key protected)
│   ├── services/
│   │   ├── spam.py          # Salted SHA-256 device hash & sliding rate limiter
│   │   ├── reference.py     # In-memory startup loader for routes & vehicles
│   │   └── validation.py    # Category & corridor verification
│   └── static/
│       └── form.html        # Mobile-first feedback form with star ratings
├── scripts/
│   ├── generate_qr.py       # Offline QR PNG generator
│   └── seed_synthetic.py    # Synthetic feedback generator (is_synthetic=True)
├── data/
│   ├── categories.json      # 14 editable grievance categories
│   └── reference_routes_vehicles.csv # 7,018 real Delhi routes & active buses
├── tests/
│   ├── test_feedback.py     # API integration tests
│   └── test_validation.py   # Anti-spam & hashing unit tests
├── .env.example
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## 🔒 Security & Privacy Engineering

1. **No Raw IP Storage**: Client IP and User-Agent are salted and hashed via SHA-256 (`device_hash`). Raw IPs are discarded immediately.
2. **Honeypot Bot Trap**: A hidden form field traps automated web scrapers. Submissions with filled honeypots are silently sunk.
3. **Sliding-Window Rate Limiting**: Max 5 submissions per device within a 10-minute window (HTTP 429).
4. **Server-Side Timestamp**: `received_at_utc` is generated strictly server-side upon arrival, preventing client clock spoofing.
5. **Synthetic Tagging**: Synthetic and test records are permanently flagged with `is_synthetic = True` to prevent contaminating empirical research metrics.

---

## 🚀 Running the Service

### 1. Local Run
```bash
# Navigate to directory
cd C:\Users\nagam\z_world\trace-feedback-fastapi\trace-feedback

# Install dependencies
pip install -r requirements.txt

# Start FastAPI server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

- Open in browser: `http://127.0.0.1:8000/feedback?r=784&v=DL1PC9421`
- Swagger Interactive API Docs: `http://127.0.0.1:8000/docs`

### 2. Generate QR Codes
```bash
python scripts/generate_qr.py
```
Output QR sticker images are saved into `scripts/qr_output/`.

### 3. Seed Synthetic Test Data
```bash
python scripts/seed_synthetic.py 150
```

### 4. Run Automated Tests
```bash
pytest tests/
```
