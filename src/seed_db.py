"""
SmartBank AI - Database Seeder Utility
Populates SQLite database (data/smartbank.db) with Demo Users, Customer Directory Leads,
Assessment History, Historical Feedback Records, and Optimizer Runs from bank-full.csv.
"""

import os
import sys
import json
import sqlite3
import pandas as pd
import numpy as np
import joblib
from datetime import datetime, timedelta, timezone

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

DB_PATH = os.path.join(BASE_DIR, "data", "smartbank.db")
DATA_PATH = os.path.join(BASE_DIR, "data", "bank-full.csv")
MODEL_PATH = os.path.join(BASE_DIR, "models", "best_pipeline.joblib")

from backend.database import init_db, get_connection

def seed_database():
    print(f"[*] Initializing & Seeding SmartBank AI Database at: {DB_PATH}")
    init_db()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Load model if available
    model = None
    if os.path.exists(MODEL_PATH):
        model = joblib.load(MODEL_PATH)
        print("[+] Loaded trained Random Forest model pipeline (11 features).")
        
    # Clear tables for clean seed
    cursor.execute("DELETE FROM customers")
    cursor.execute("DELETE FROM assessments")
    cursor.execute("DELETE FROM customer_predictions")
    cursor.execute("DELETE FROM campaign_feedback")
    cursor.execute("DELETE FROM campaign_optimizer_runs")
    cursor.execute("DELETE FROM model_telemetry")
    
    now = datetime.now(timezone.utc)
    
    # 1. Seed Demo Customers and Assessments from dataset
    if os.path.exists(DATA_PATH) and model is not None:
        df = pd.read_csv(DATA_PATH, sep=";")
        sample = df.sample(n=60, random_state=42).copy()
        
        pre_cols = ['job', 'marital', 'education', 'default', 'housing', 'loan', 'poutcome', 'age', 'balance', 'previous', 'pdays']
        X = sample[pre_cols].copy()
        probs = model.predict_proba(X)[:, 1]
        
        first_names = ["Marcus", "Elena", "Sophia", "David", "Aisha", "Liam", "Olivia", "Ethan", "Amara", "Lucas", "Maya", "Noah", "Chloe", "Julian", "Isabella", "Alexander", "Zoe", "Gabriel", "Mia", "Benjamin", "Charlotte", "Daniel", "Emily", "Henry", "Grace", "Jack", "Lily", "Samuel", "Ava", "William"]
        last_names = ["Vance", "Rostova", "Chen", "Miller", "Diallo", "O'Connor", "Dubois", "Kim", "Patel", "Santoro", "Larsen", "Kovacs", "Moreau", "Novak", "Tanaka", "Mendoza", "Schneider", "Costa", "Nielsen", "Berg", "Lindqvist", "Fischer", "Rossi", "Petrov", "Santos", "Morin", "Gomez", "Kowalski", "Dupont", "Yamamoto"]
        
        # Seed 30 customer leads
        for i, (idx, row) in enumerate(sample.iloc[:30].iterrows()):
            prob = float(probs[i])
            score = int(round(prob * 100))
            priority = "HIGH" if score >= 65 else ("MEDIUM" if score >= 40 else "LOW")
            cid = f"CUST-{1001 + i}"
            cname = f"{first_names[i % len(first_names)]} {last_names[i % len(last_names)]}"
            cemail = f"{cname.lower().replace(' ', '.')}@example.com"
            cphone = f"+1 (555) {100 + i:03d}-{2000 + i:04d}"
            
            cursor.execute("""
            INSERT INTO customers (
                customer_id, name, email, phone, age, job, marital, education,
                default_credit, balance, housing, loan, poutcome, pdays, previous,
                source, last_opportunity_score, last_priority, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cid, cname, cemail, cphone,
                int(row['age']), str(row['job']), str(row['marital']), str(row['education']),
                str(row['default']), float(row['balance']), str(row['housing']), str(row['loan']),
                str(row['poutcome']), int(row['pdays']), int(row['previous']),
                "demo", score, priority, (now - timedelta(days=30-i)).isoformat()
            ))
            
            # Seed corresponding assessment
            action = "Priority Outreach: Assign Senior Relationship Manager with preferential term deposit incentive." if priority == "HIGH" else (
                "Digital Nudge: Dispatch tailored mobile banking prompt followed by standard campaign call." if priority == "MEDIUM" else
                "Deprioritize Outreach: Suppress direct calling to preserve agent hours; include in low-cost monthly digest."
            )
            
            signals = []
            if row['poutcome'] == 'success':
                signals.append({"factor": "Previous Campaign Success", "impact": "+Strong Positive (+28%)", "type": "positive", "weight": 95})
            if row['housing'] == 'no':
                signals.append({"factor": "No Housing Loan Obligation", "impact": "+Positive (+14%)", "type": "positive", "weight": 70})
            if row['balance'] > 2000:
                signals.append({"factor": "Healthy Account Balance (>€2,000)", "impact": "+Positive (+18%)", "type": "positive", "weight": 82})
            elif row['balance'] < 100:
                signals.append({"factor": "Low Account Balance (<€100)", "impact": "-Restraining (-12%)", "type": "negative", "weight": 60})
            if row['age'] >= 60:
                signals.append({"factor": "Retirement Cohort Demographics", "impact": "+Positive (+15%)", "type": "positive", "weight": 75})
            if not signals:
                signals.append({"factor": "Standard Demographic Baseline", "impact": "Neutral Baseline", "type": "neutral", "weight": 30})
                
            input_feats = {
                "age": int(row['age']),
                "job": str(row['job']),
                "marital": str(row['marital']),
                "education": str(row['education']),
                "default": str(row['default']),
                "balance": float(row['balance']),
                "housing": str(row['housing']),
                "loan": str(row['loan']),
                "poutcome": str(row['poutcome']),
                "pdays": int(row['pdays']),
                "previous": int(row['previous'])
            }
            
            cursor.execute("""
            INSERT INTO assessments (
                customer_id, customer_name, timestamp, model_version,
                probability, opportunity_score, campaign_priority, prediction_label,
                next_best_action, predictive_signals, input_features
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cid, cname, (now - timedelta(hours=i*2)).isoformat(),
                "v1.0.0 (Random Forest)", round(prob, 4), score, priority,
                "Likely to Subscribe" if prob >= 0.50 else "Unlikely to Subscribe",
                action, json.dumps(signals), json.dumps(input_feats)
            ))
            
        print("[+] Seeded 30 customer leads and assessment logs.")
        
        # 2. Seed 50 historical campaign feedback rows
        for i, (idx, row) in enumerate(sample.iloc[:50].iterrows()):
            prob = float(probs[i])
            score = int(round(prob * 100))
            priority = "HIGH" if score >= 65 else ("MEDIUM" if score >= 40 else "LOW")
            actual_y = str(row['y']).strip().lower()
            pred_binary = "yes" if prob >= 0.50 else "no"
            match = 1 if pred_binary == actual_y else 0
            contact_date = (now - timedelta(days=(50 - i))).strftime("%Y-%m-%d")
            
            cursor.execute("""
            INSERT INTO campaign_feedback (
                customer_ref, predicted_probability, opportunity_score,
                campaign_priority, actual_outcome, outcome_match, contact_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                f"CUST-{1001 + i}",
                round(prob, 4),
                score,
                priority,
                actual_y,
                match,
                contact_date
            ))
        print("[+] Seeded 50 historical campaign feedback records.")
        
        # 3. Seed 5 Campaign Optimizer Runs
        optimizer_benchmarks = [
            (500, 185, 192, 96, 27, 324.5, 0.649, 5.55),
            (1000, 252, 385, 271, 92, 548.0, 0.548, 4.68),
            (2000, 318, 645, 710, 327, 898.0, 0.449, 3.84),
            (3500, 348, 825, 1405, 922, 1220.0, 0.349, 2.98),
            (5000, 352, 945, 2005, 1698, 1425.0, 0.285, 2.44)
        ]
        for cap, a, b, c, d, exp_conv, avg_p, lift in optimizer_benchmarks:
            cursor.execute("""
            INSERT INTO campaign_optimizer_runs (
                timestamp, target_capacity, pool_size, tier_a_count, tier_b_count,
                tier_c_count, tier_d_count, expected_conversions, avg_probability, optimized_yield_lift, analyst_user
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                (now - timedelta(hours=len(optimizer_benchmarks) - optimizer_benchmarks.index((cap, a, b, c, d, exp_conv, avg_p, lift)))).isoformat(),
                cap, 5000, a, b, c, d, exp_conv, avg_p, lift, "Alex Mercer (Campaign Analyst)"
            ))
        print("[+] Seeded 5 campaign optimizer benchmarks.")
        
        # 4. Seed Model Health Telemetry
        cursor.execute("""
        INSERT INTO model_telemetry (
            timestamp, model_name, model_version, training_records,
            active_features_count, health_status, avg_inferred_probability,
            low_opportunity_pct, medium_opportunity_pct, high_opportunity_pct, psi_score
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            now.isoformat(),
            "Random Forest Classifier (Balanced Ensemble)",
            "v1.0.0",
            45211,
            11,
            "HEALTHY_PRODUCTION_READY",
            0.248,
            63.8,
            21.5,
            14.7,
            0.024
        ))
        print("[+] Seeded model telemetry records.")
        
    conn.commit()
    conn.close()
    print(f"[SUCCESS] Database successfully seeded at {DB_PATH}")

if __name__ == "__main__":
    seed_database()
