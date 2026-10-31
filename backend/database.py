import sqlite3
import datetime

DB_PATH = "medical_records.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS history
                 (user_id TEXT, date TEXT, test_name TEXT, value REAL, unit TEXT)''')
    
    # Check if empty, seed with initial demo baseline history if needed
    c.execute("SELECT COUNT(*) FROM history")
    count = c.fetchone()[0]
    if count == 0:
        demo_points = [
            ("demo_user", "2025-01-15", "LDL Cholesterol", 148.0, "mg/dL"),
            ("demo_user", "2025-01-15", "Hemoglobin", 13.1, "g/dL"),
            ("demo_user", "2025-02-15", "LDL Cholesterol", 152.0, "mg/dL"),
            ("demo_user", "2025-02-15", "Hemoglobin", 12.7, "g/dL"),
            ("demo_user", "2025-03-18", "LDL Cholesterol", 165.0, "mg/dL"),
            ("demo_user", "2025-03-18", "Hemoglobin", 11.2, "g/dL"),
            ("demo_user", "2025-04-10", "LDL Cholesterol", 158.0, "mg/dL"),
            ("demo_user", "2025-04-10", "Hemoglobin", 11.5, "g/dL"),
            ("demo_user", "2025-05-12", "LDL Cholesterol", 161.0, "mg/dL"),
            ("demo_user", "2025-05-12", "Hemoglobin", 11.4, "g/dL"),
        ]
        c.executemany("INSERT INTO history VALUES (?, ?, ?, ?, ?)", demo_points)
    
    conn.commit()
    conn.close()

def save_results(user_id, date, findings):
    if not date:
        date = datetime.date.today().isoformat()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for f in findings:
        try:
            val = float(f.value)
            c.execute("INSERT INTO history VALUES (?, ?, ?, ?, ?)", 
                      (user_id, date, f.name, val, f.unit))
        except Exception:
            pass
    conn.commit()
    conn.close()

def get_trends(user_id, metric="both"):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    metric_clean = (metric or "both").lower()
    
    if metric_clean in ("both", "all", ""):
        c.execute("""
            SELECT date, test_name, value, unit 
            FROM history 
            WHERE user_id=? OR user_id='demo_user'
            ORDER BY date ASC
        """, (user_id,))
    else:
        # Match test_name containing the metric keyword (e.g. 'ldl' matches 'LDL Cholesterol')
        pattern = f"%{metric_clean}%"
        c.execute("""
            SELECT date, test_name, value, unit 
            FROM history 
            WHERE (user_id=? OR user_id='demo_user') AND LOWER(test_name) LIKE ?
            ORDER BY date ASC
        """, (user_id, pattern))
        
    rows = c.fetchall()
    conn.close()
    
    return [{"date": r[0], "metric": r[1], "value": r[2], "unit": r[3]} for r in rows]
