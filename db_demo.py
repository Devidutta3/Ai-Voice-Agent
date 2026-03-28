from __future__ import annotations
from sqlalchemy import text
from Database import engine, init_db

def run_sql(query: str):
    init_db()
    with engine.begin() as conn:
        result = conn.execute(text(query))
        return result.fetchall() if result.returns_rows else result.rowcount

query = """INSERT INTO appointments (patient_name, reason, start_time, canceled, created_at) VALUES ('John Doe', 'Checkup', '2026-01-24 14:30:00', 0, '2026-01-24 14:30:00')"""

print(run_sql(query))
rows = run_sql("SELECT * FROM appointments")
print(rows)