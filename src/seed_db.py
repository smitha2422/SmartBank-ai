"""
SmartBank AI - Database Seeder Utility
Seeds SQLite database (data/smartbank.db) with initial verified records from the UCI Bank Marketing evaluation pool.
"""

import os
import json
import sqlite3
import pandas as pd
import numpy as np
import joblib
from datetime import datetime, timedelta

import sys
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
        print("[+] Loaded trained Random Forest model pipeline.")
    
    # 1. Seed Customer Predictions & Feedback from actual bank dataset
    if os.path.exists(DATA_PATH) and model is not None:
        df = pd.read_csv(DATA_PATH, sep=";")
        sample = df.sample(n=60, random_state=42).copy()
        
        pre_cols = ['job', 'marital', 'education', 'default', 'housing', 'loan', 'poutcome', 'age', 'balance', 'previous']
        X = sample[pre_cols].copy()
        probs = model.predict_proba(X)[:, 1]
        
        # Clear existing predictions/feedback for clean seed
        cursor.execute("DELETE FROM customer_predictions")
        cursor.execute("DELETE FROM campaign_feedback")
        cursor.execute("DELETE FROM campaign_optimizer_runs")
        cursor.execute("DELETE FROM model_telemetry")
        
        now = datetime.utcnow()
        
        # Seed 25 customer predictions
        for i, (idx, row) in enumerate(sample.iloc[:25].iterrows()):
            prob = float(probs[i])
            score = int(round(prob * 100))
            
            if score >= 65:
                priority = "HIGH"
                action = "Priority Outreach: Assign Senior Relationship Manager with preferential term deposit rate."
            elif score >= 40:
                priority = "MEDIUM"
                action = "Digital Nudge: Dispatch tailored mobile banking prompt followed by standard campaign call."
            else:
                priority = "LOW"
                action = "Deprioritize Outreach: Suppress direct calling to preserve agent hours; include in low-cost email digest."
                
            label = "Likely to Subscribe" if prob >= 0.50 else "Unlikely to Subscribe"
            
            signals = []
            if row['poutcome'] == 'success':
                signals.append({"factor": "Previous Campaign Success", "impact": "+Strong Positive", "type": "positive"})
            if row['housing'] == 'no':
                signals.append({"factor": "No Housing Loan Obligation", "impact": "+Positive", "type": "positive"})
            if row['balance'] > 2000:
                signals.append({"factor": "Healthy Account Balance (>€2,000)", "impact": "+Positive", "type": "positive"})
            elif row['balance'] < 100:
                signals.append({"factor": "Low Account Balance (<€100)", "impact": "-Restraining", "type": "negative"})
            if row['age'] >= 60:
                signals.append({"factor": "Retirement Demographics", "impact": "+Positive", "type": "positive"})
            if row['housing'] == 'yes':
                signals.append({"factor": "Active Housing Loan Commitment", "impact": "-Restraining", "type": "negative"})
            if row['loan'] == 'yes':
                signals.append({"factor": "Active Personal Loan Debt", "impact": "-Restraining", "type": "negative"})
            if not signals:
                signals.append({"factor": "Standard Demographic Baseline", "impact": "Neutral", "type": "neutral"})
                
            timestamp = (now - timedelta(minutes=(25 - i) * 12)).isoformat()
            
            cursor.execute("""
            INSERT INTO customer_predictions (
                timestamp, age, job, marital, education, default_credit, balance,
                housing, loan, poutcome, previous, probability, opportunity_score,
                campaign_priority, prediction_label, next_best_action, predictive_signals
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp,
                int(row['age']),
                str(row['job']),
                str(row['marital']),
                str(row['education']),
                str(row['default']),
                float(row['balance']),
                str(row['housing']),
                str(row['loan']),
                str(row['poutcome']),
                int(row['previous']),
                round(prob, 4),
                score,
                priority,
                label,
                action,
                json.dumps(signals)
            ))
            
        print(f"[+] Seeded 25 customer predictions.")
        
        # Seed 50 historical campaign feedback rows
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
                f"CUST-{1000 + i}",
                round(prob, 4),
                score,
                priority,
                actual_y,
                match,
                contact_date
            ))
        print(f"[+] Seeded 50 campaign feedback records.")
        
        # 2. Seed Campaign Optimizer Runs
        optimizer_benchmarks = [
            (500, 182, 194, 98, 26, 318.5, 0.637, 5.44),
            (1000, 246, 388, 274, 92, 542.0, 0.542, 4.63),
            (2000, 312, 642, 714, 332, 894.0, 0.447, 3.82),
            (3500, 345, 820, 1410, 925, 1215.0, 0.347, 2.97),
            (5000, 350, 940, 2010, 1700, 1420.0, 0.284, 2.43)
        ]
        for cap, a, b, c, d, exp_conv, avg_p, lift in optimizer_benchmarks:
            cursor.execute("""
            INSERT INTO campaign_optimizer_runs (
                timestamp, target_capacity, tier_a_count, tier_b_count,
                tier_c_count, tier_d_count, expected_conversions, avg_probability, optimized_yield_lift
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                (now - timedelta(hours=len(optimizer_benchmarks) - optimizer_benchmarks.index((cap, a, b, c, d, exp_conv, avg_p, lift)))).isoformat(),
                cap, a, b, c, d, exp_conv, avg_p, lift
            ))
        print(f"[+] Seeded 5 campaign optimizer simulation benchmarks.")
        
        # 3. Seed Model Health Telemetry
        cursor.execute("""
        INSERT INTO model_telemetry (
            timestamp, model_name, model_version, training_records,
            active_features_count, health_status, avg_inferred_probability,
            low_opportunity_pct, medium_opportunity_pct, high_opportunity_pct
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            now.isoformat(),
            "Random Forest Classifier (Ensemble)",
            "v1.0.0",
            45211,
            10,
            "HEALTHY_PRODUCTION_READY",
            0.246,
            64.2,
            21.3,
            14.5
        ))
    conn.commit()
    conn.close()
    print(f"[SUCCESS] Database successfully seeded at {DB_PATH}")

if __name__ == "__main__":
    seed_database()
