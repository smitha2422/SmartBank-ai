"""
SmartBank AI - Database Engine
Embedded SQLite storage for customer predictions, campaign optimizer runs, feedback intelligence, and model telemetry.
"""

import os
import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "smartbank.db")

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes SQLite schema for SmartBank AI decision platform."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Customer Predictions Table
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
        previous INTEGER NOT NULL,
        probability REAL NOT NULL,
        opportunity_score INTEGER NOT NULL,
        campaign_priority TEXT NOT NULL,
        prediction_label TEXT NOT NULL,
        next_best_action TEXT NOT NULL,
        predictive_signals TEXT
    )
    """)
    
    # 2. Campaign Optimizer Runs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS campaign_optimizer_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        target_capacity INTEGER NOT NULL,
        tier_a_count INTEGER NOT NULL,
        tier_b_count INTEGER NOT NULL,
        tier_c_count INTEGER NOT NULL,
        tier_d_count INTEGER NOT NULL,
        expected_conversions REAL NOT NULL,
        avg_probability REAL NOT NULL,
        optimized_yield_lift REAL NOT NULL
    )
    """)
    
    # 3. Campaign Feedback Intelligence Table (Predicted vs Actual)
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
    
    # 4. Model Health & Drift Telemetry Table
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
        high_opportunity_pct REAL
    )
    """)
    
    conn.commit()
    conn.close()
    print(f"[SmartBank DB] Initialized SQLite database at '{DB_PATH}'")

def log_prediction(features: Dict[str, Any], prob: float, score: int, priority: str, label: str, action: str, signals: List[Dict[str, Any]]):
    """Stores individual customer prediction event."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    INSERT INTO customer_predictions (
        timestamp, age, job, marital, education, default_credit, balance,
        housing, loan, poutcome, previous, probability, opportunity_score,
        campaign_priority, prediction_label, next_best_action, predictive_signals
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.utcnow().isoformat(),
        features.get("age"),
        features.get("job"),
        features.get("marital"),
        features.get("education"),
        features.get("default", "no"),
        features.get("balance"),
        features.get("housing", "no"),
        features.get("loan", "no"),
        features.get("poutcome", "unknown"),
        features.get("previous", 0),
        prob,
        score,
        priority,
        label,
        action,
        json.dumps(signals)
    ))
    
    conn.commit()
    conn.close()

def get_recent_predictions(limit: int = 15) -> List[Dict[str, Any]]:
    """Retrieves recent prediction history."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customer_predictions ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for r in rows:
        item = dict(r)
        if item.get("predictive_signals"):
            try:
                item["predictive_signals"] = json.loads(item["predictive_signals"])
            except Exception:
                pass
        results.append(item)
    return results

def log_optimizer_run(capacity: int, counts: Dict[str, int], expected_conv: float, avg_p: float, lift: float):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO campaign_optimizer_runs (
        timestamp, target_capacity, tier_a_count, tier_b_count,
        tier_c_count, tier_d_count, expected_conversions, avg_probability, optimized_yield_lift
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.utcnow().isoformat(),
        capacity,
        counts.get("A", 0),
        counts.get("B", 0),
        counts.get("C", 0),
        counts.get("D", 0),
        expected_conv,
        avg_p,
        lift
    ))
    conn.commit()
    conn.close()

def get_feedback_records(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieves campaign feedback learning records."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM campaign_feedback ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_optimizer_history(limit: int = 10) -> List[Dict[str, Any]]:
    """Retrieves optimizer simulation run history."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM campaign_optimizer_runs ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_latest_telemetry() -> Optional[Dict[str, Any]]:
    """Retrieves latest model health & telemetry log."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM model_telemetry ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

# Auto-initialize database on import
init_db()
