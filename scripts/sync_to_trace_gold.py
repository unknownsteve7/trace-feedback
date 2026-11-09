"""
scripts/sync_to_trace_gold.py
─────────────────────────────────────────────────────────────
ETL Sync: Pulls grievances from feedback.db (FastAPI service)
and loads them into TRACE Gold Layer PostgreSQL (fact_complaints).
Demonstrates end-to-end integration:
  QR Scan -> Mobile Form -> FastAPI DB -> Gold Star Schema.

Uses asyncpg (pre-installed).

Usage:
    python scripts/sync_to_trace_gold.py
"""

import os
import sys
import sqlite3
import asyncio
from pathlib import Path
from datetime import datetime
import asyncpg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

SQLITE_DB = ROOT / "feedback.db"

PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = int(os.getenv("PG_PORT", "5432"))
PG_DB   = os.getenv("PG_DATABASE", "trace_db")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASS = os.getenv("PG_PASSWORD", "trace_pass")

async def sync():
    if not SQLITE_DB.exists():
        print(f"Error: {SQLITE_DB} not found. Run seed_synthetic.py or submit grievances first.")
        return

    print("Connecting to local feedback database (SQLite)...")
    sq_conn = sqlite3.connect(SQLITE_DB)
    sq_conn.row_factory = sqlite3.Row
    sq_cur = sq_conn.cursor()
    sq_cur.execute("""
        SELECT feedback_id, received_at_utc, route_id, vehicle_id, category, rating, comment, is_synthetic
        FROM feedback
        ORDER BY received_at_utc ASC
    """)
    feedbacks = sq_cur.fetchall()
    sq_conn.close()

    print(f"Read {len(feedbacks)} feedback records from SQLite.")

    print(f"Connecting to PostgreSQL Gold Layer ({PG_DB} on {PG_HOST}:{PG_PORT})...")
    conn = await asyncpg.connect(
        host=PG_HOST,
        port=PG_PORT,
        database=PG_DB,
        user=PG_USER,
        password=PG_PASS
    )

    try:
        # 1. Fetch route mappings
        route_rows = await conn.fetch("SELECT route_id, route_key FROM dim_route WHERE is_current = TRUE;")
        route_map = {str(r["route_id"]): r["route_key"] for r in route_rows}

        # 2. Fetch date mappings
        date_rows = await conn.fetch("SELECT full_date, date_id FROM dim_date;")
        date_map = {r["full_date"].isoformat(): r["date_id"] for r in date_rows}

        insert_records = []
        for fb in feedbacks:
            rec_dt = datetime.fromisoformat(fb["received_at_utc"].replace("Z", "+00:00"))
            dt_str = rec_dt.strftime("%Y-%m-%d")

            route_key = route_map.get(fb["route_id"])
            date_id   = date_map.get(dt_str)
            comment_text = fb["comment"] or f"Rating: {fb['rating']}/5 for {fb['category']}"

            insert_records.append((
                fb["feedback_id"],
                route_key,
                date_id,
                None,             # stop_id
                fb["vehicle_id"],
                fb["category"],
                comment_text,
                rec_dt,
                bool(fb["is_synthetic"])
            ))

        # 3. Upsert into fact_complaints
        stmt = """
            INSERT INTO fact_complaints
                (complaint_id, route_key, date_id, stop_id, vehicle_id,
                 category, complaint_text, submitted_at, is_simulated)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT (complaint_id) DO NOTHING;
        """
        result = await conn.executemany(stmt, insert_records)
        print("Upsert executed successfully.")

        # 4. Total count check
        total_count = await conn.fetchval("SELECT COUNT(*) FROM fact_complaints;")
        live_count = await conn.fetchval("SELECT COUNT(*) FROM fact_complaints WHERE is_simulated = FALSE;")
        synth_count = await conn.fetchval("SELECT COUNT(*) FROM fact_complaints WHERE is_simulated = TRUE;")

        print("--------------------------------------------------")
        print("TRACE Gold Layer Sync Summary:")
        print(f"  Total Complaints in Postgres: {total_count}")
        print(f"  Synthetic / Pilot Rows:      {synth_count}")
        print(f"  Live Submissions:             {live_count}")
        print("--------------------------------------------------")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(sync())
