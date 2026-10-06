"""
SmartBank AI - Database Engine
SQLite persistence for Users, Customers, Assessments, Campaign Optimization, Feedback, and Telemetry.
"""

import os
import sqlite3
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "smartbank.db")

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes SQLite schema for SmartBank AI platform."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Users Table (Demo Auth Roles)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        name TEXT NOT NULL,
        role TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)
    
    # 2. Customers Table (Customer Profile & Pre-Contact Attributes)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        age INTEGER NOT NULL,
        job TEXT NOT NULL,
        marital TEXT NOT NULL,
        education TEXT NOT NULL,
        default_credit TEXT NOT NULL DEFAULT 'no',
        balance REAL NOT NULL DEFAULT 0.0,
        housing TEXT NOT NULL DEFAULT 'no',
        loan TEXT NOT NULL DEFAULT 'no',
        poutcome TEXT NOT NULL DEFAULT 'unknown',
        pdays INTEGER NOT NULL DEFAULT -1,
        previous INTEGER NOT NULL DEFAULT 0,
        source TEXT NOT NULL DEFAULT 'demo',
        last_opportunity_score INTEGER,
        last_priority TEXT,
        created_at TEXT NOT NULL
    )
    """)
    
    # 3. Customer Assessments / Predictions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS assessments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id TEXT NOT NULL,
        customer_name TEXT,
        timestamp TEXT NOT NULL,
        model_version TEXT NOT NULL,
        probability REAL NOT NULL,
        opportunity_score INTEGER NOT NULL,
        campaign_priority TEXT NOT NULL,
        prediction_label TEXT NOT NULL,
        next_best_action TEXT NOT NULL,
        predictive_signals TEXT,
        input_features TEXT
    )
    """)
    
    # Backwards-compatible view or table for customer_predictions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customer_predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        age INTEGER NOT NULL,
        job TEXT NOT NULL,
        marital TEXT NOT NULL,
        education TEXT NOT NULL,
        default_credit TEXT NOT NULL,
        balance REAL NOT NULL,
        housing TEXT NOT NULL,
        loan TEXT NOT NULL,
        poutcome TEXT NOT NULL,
        pdays INTEGER NOT NULL DEFAULT -1,
        previous INTEGER NOT NULL,
        probability REAL NOT NULL,
        opportunity_score INTEGER NOT NULL,
        campaign_priority TEXT NOT NULL,
        prediction_label TEXT NOT NULL,
        next_best_action TEXT NOT NULL,
        predictive_signals TEXT
    )
    """)
    
    # 4. Campaign Optimizer Runs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS campaign_optimizer_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        target_capacity INTEGER NOT NULL,
        pool_size INTEGER NOT NULL DEFAULT 5000,
        tier_a_count INTEGER NOT NULL,
        tier_b_count INTEGER NOT NULL,
        tier_c_count INTEGER NOT NULL,
        tier_d_count INTEGER NOT NULL,
        expected_conversions REAL NOT NULL,
        avg_probability REAL NOT NULL,
        optimized_yield_lift REAL NOT NULL,
        analyst_user TEXT NOT NULL DEFAULT 'Campaign Analyst'
    )
    """)
    
    # 5. Campaign Feedback Intelligence Table (Predicted vs Actual)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS campaign_feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_ref TEXT NOT NULL,
        predicted_probability REAL NOT NULL,
        opportunity_score INTEGER NOT NULL,
        campaign_priority TEXT NOT NULL,
        actual_outcome TEXT NOT NULL,
        outcome_match INTEGER NOT NULL,
        contact_date TEXT NOT NULL
    )
    """)
    
    # 6. Model Health & Drift Telemetry Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS model_telemetry (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        model_name TEXT NOT NULL,
        model_version TEXT NOT NULL,
        training_records INTEGER NOT NULL,
        active_features_count INTEGER NOT NULL,
        health_status TEXT NOT NULL,
        avg_inferred_probability REAL,
        low_opportunity_pct REAL,
        medium_opportunity_pct REAL,
        high_opportunity_pct REAL,
        psi_score REAL DEFAULT 0.024
    )
    """)
    
    # Column migration checks for existing tables
    def ensure_column(table, column, col_type):
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
        except sqlite3.OperationalError:
            pass # column already exists
            
    ensure_column("campaign_optimizer_runs", "pool_size", "INTEGER NOT NULL DEFAULT 5000")
    ensure_column("campaign_optimizer_runs", "analyst_user", "TEXT NOT NULL DEFAULT 'Campaign Analyst'")
    ensure_column("model_telemetry", "psi_score", "REAL DEFAULT 0.024")
    ensure_column("customer_predictions", "pdays", "INTEGER NOT NULL DEFAULT -1")
    ensure_column("customers", "pdays", "INTEGER NOT NULL DEFAULT -1")

    # Ensure default demo users exist
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
        INSERT INTO users (email, password, name, role, created_at) VALUES 
        ('analyst@smartbank.ai', 'demo123', 'Alex Mercer (Campaign Analyst)', 'Campaign Analyst', ?),
        ('demo@smartbank.ai', 'demo123', 'Demo Analyst (Gupio Reviewer)', 'Campaign Analyst', ?),
        ('admin@smartbank.ai', 'admin123', 'Sarah Vance (Administrator)', 'Administrator', ?)
        """, (now, now, now))
    
    conn.commit()
    conn.close()

# -------------------------------------------------------------
# USER AUTHENTICATION
# -------------------------------------------------------------
def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE LOWER(email) = LOWER(?) AND password = ?", (email.strip(), password.strip()))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "id": row["id"],
            "email": row["email"],
            "name": row["name"],
            "role": row["role"]
        }
    return None

# -------------------------------------------------------------
# CUSTOMER MANAGEMENT
# -------------------------------------------------------------
def list_customers(search: Optional[str] = None, priority: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM customers WHERE 1=1"
    params = []
    
    if search:
        s = f"%{search.strip()}%"
        query += " AND (customer_id LIKE ? OR name LIKE ? OR job LIKE ? OR email LIKE ?)"
        params.extend([s, s, s, s])
        
    if priority and priority.upper() in ["HIGH", "MEDIUM", "LOW"]:
        query += " AND last_priority = ?"
        params.append(priority.upper())
        
    query += " ORDER BY id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_customer_by_id(customer_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customers WHERE customer_id = ? OR id = ?", (customer_id, customer_id))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def create_customer(data: Dict[str, Any]) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    
    cid = data.get("customer_id")
    if not cid:
        cursor.execute("SELECT MAX(id) FROM customers")
        max_id = cursor.fetchone()[0] or 1000
        cid = f"CUST-{max_id + 1}"
        
    now = datetime.now(timezone.utc).isoformat()
    cursor.execute("""
    INSERT INTO customers (
        customer_id, name, email, phone, age, job, marital, education,
        default_credit, balance, housing, loan, poutcome, pdays, previous, source, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        cid,
        data.get("name", "New Lead"),
        data.get("email", f"{cid.lower()}@example.com"),
        data.get("phone", "+1 555-0199"),
        int(data.get("age", 40)),
        str(data.get("job", "technician")).lower(),
        str(data.get("marital", "married")).lower(),
        str(data.get("education", "secondary")).lower(),
        str(data.get("default", data.get("default_credit", "no"))).lower(),
        float(data.get("balance", 1500.0)),
        str(data.get("housing", "no")).lower(),
        str(data.get("loan", "no")).lower(),
        str(data.get("poutcome", "unknown")).lower(),
        int(data.get("pdays", -1)),
        int(data.get("previous", 0)),
        data.get("source", "manual"),
        now
    ))
    conn.commit()
    conn.close()
    return get_customer_by_id(cid)

def update_customer_assessment_score(customer_id: str, score: int, priority: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE customers SET last_opportunity_score = ?, last_priority = ? WHERE customer_id = ?", (score, priority, customer_id))
    conn.commit()
    conn.close()

# -------------------------------------------------------------
# ASSESSMENTS & PREDICTIONS
# -------------------------------------------------------------
def log_assessment(data: Dict[str, Any]):
    conn = get_connection()
    cursor = conn.cursor()
    
    cid = data.get("customer_id", "CUST-GUEST")
    cname = data.get("customer_name", "Prospective Client")
    now = datetime.now(timezone.utc).isoformat()
    
    cursor.execute("""
    INSERT INTO assessments (
        customer_id, customer_name, timestamp, model_version,
        probability, opportunity_score, campaign_priority, prediction_label,
        next_best_action, predictive_signals, input_features
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        cid,
        cname,
        now,
        data.get("model_version", "v1.0.0 (Random Forest)"),
        float(data.get("probability", 0.0)),
        int(data.get("opportunity_score", 0)),
        data.get("campaign_priority", "LOW"),
        data.get("prediction_label", "Unlikely to Subscribe"),
        data.get("next_best_action", "Standard Outreach"),
        json.dumps(data.get("predictive_signals", [])),
        json.dumps(data.get("input_features", {}))
    ))
    
    # Also log to customer_predictions table
    feat = data.get("input_features", {})
    cursor.execute("""
    INSERT INTO customer_predictions (
        timestamp, age, job, marital, education, default_credit, balance,
        housing, loan, poutcome, pdays, previous, probability, opportunity_score,
        campaign_priority, prediction_label, next_best_action, predictive_signals
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        now,
        feat.get("age", 40),
        feat.get("job", "management"),
        feat.get("marital", "married"),
        feat.get("education", "tertiary"),
        feat.get("default", "no"),
        feat.get("balance", 1000.0),
        feat.get("housing", "no"),
        feat.get("loan", "no"),
        feat.get("poutcome", "unknown"),
        feat.get("pdays", -1),
        feat.get("previous", 0),
        float(data.get("probability", 0.0)),
        int(data.get("opportunity_score", 0)),
        data.get("campaign_priority", "LOW"),
        data.get("prediction_label", "Unlikely to Subscribe"),
        data.get("next_best_action", ""),
        json.dumps(data.get("predictive_signals", []))
    ))
    
    # Update customer record if matching customer exists
    cursor.execute("UPDATE customers SET last_opportunity_score = ?, last_priority = ? WHERE customer_id = ?", 
                   (int(data.get("opportunity_score", 0)), data.get("campaign_priority", "LOW"), cid))
    
    conn.commit()
    conn.close()

def get_recent_assessments(limit: int = 20) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM assessments ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for r in rows:
        item = dict(r)
        if item.get("predictive_signals"):
            try: item["predictive_signals"] = json.loads(item["predictive_signals"])
            except: pass
        if item.get("input_features"):
            try: item["input_features"] = json.loads(item["input_features"])
            except: pass
        results.append(item)
    return results

def get_assessments_for_customer(customer_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM assessments WHERE customer_id = ? ORDER BY id DESC", (customer_id,))
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for r in rows:
        item = dict(r)
        if item.get("predictive_signals"):
            try: item["predictive_signals"] = json.loads(item["predictive_signals"])
            except: pass
        if item.get("input_features"):
            try: item["input_features"] = json.loads(item["input_features"])
            except: pass
        results.append(item)
    return results

# -------------------------------------------------------------
# OPTIMIZER, FEEDBACK & TELEMETRY
# -------------------------------------------------------------
def log_optimizer_run(capacity: int, counts: Dict[str, int], expected_conv: float, avg_p: float, lift: float, pool_size: int = 5000, analyst: str = "Campaign Analyst"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO campaign_optimizer_runs (
        timestamp, target_capacity, pool_size, tier_a_count, tier_b_count,
        tier_c_count, tier_d_count, expected_conversions, avg_probability, optimized_yield_lift, analyst_user
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now(timezone.utc).isoformat(),
        capacity,
        pool_size,
        counts.get("A", 0),
        counts.get("B", 0),
        counts.get("C", 0),
        counts.get("D", 0),
        expected_conv,
        avg_p,
        lift,
        analyst
    ))
    conn.commit()
    conn.close()

def get_feedback_records(limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM campaign_feedback ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_optimizer_history(limit: int = 10) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM campaign_optimizer_runs ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_latest_telemetry() -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM model_telemetry ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

# Auto-initialize database on import
init_db()
