# SmartBank AI — AI Campaign Intelligence & Customer Decision Platform

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.5%2B-F7931E.svg)](https://scikit-learn.org/)
[![SQLite 3](https://img.shields.io/badge/SQLite-3-003B57.svg)](https://www.sqlite.org/)
[![PWA Ready](https://img.shields.io/badge/PWA-Ready-5A0FC8.svg)](https://web.dev/progressive-web-apps/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Predict. Prioritize. Act.**  
> An enterprise-grade, leakage-safe AI Campaign Intelligence & Decision Engine designed to evaluate customer term-deposit propensity, optimize team calling capacity, and automate deterministic next best actions before direct outreach begins.

---

## 🏛️ 1. Platform Positioning & Architecture

SmartBank AI is designed not just as a one-off bank classifier, but as a **reusable AI campaign-intelligence platform** demonstrated on the UCI Bank Marketing dataset.

```
                            SMARTBANK AI
                                 │
                         DEMO AUTHENTICATION
                   (Analyst / Admin Demo Roles)
                                 │
                        CAMPAIGN DASHBOARD
                                 │
                ┌────────────────┴────────────────┐
                ▼                                 ▼
       CUSTOMER MANAGEMENT                CAMPAIGN DATA POOL
                │                                 │
                └────────────────┬────────────────┘
                                 ▼
                    PRE-CONTACT DATA VALIDATION
                                 │
                                 ▼
                     LEAKAGE GUARD ENFORCEMENT
            (Excluded: duration, contact, day, month, campaign)
                                 │
                                 ▼
                   BALANCED ML PIPELINE (RF v1.0)
                                 │
                ┌────────────────┴────────────────┐
                ▼                                 ▼
      PROBABILITY INFERENCE               PREDICTIVE SIGNALS
                │                                 │
                └────────────────┬────────────────┘
                                 ▼
                       OPPORTUNITY SCORE (0–100)
                                 │
                                 ▼
                       CAMPAIGN PRIORITY TRIAGE
                         (HIGH / MEDIUM / LOW)
                                 │
                                 ▼
                     AI CAMPAIGN OPTIMIZER (3.8x Lift)
                                 │
                                 ▼
                    DETERMINISTIC NEXT BEST ACTION
                                 │
                                 ▼
                      SQLITE PERSISTENCE ENGINE
                         (data/smartbank.db)
                                 │
                                 ▼
                     CAMPAIGN FEEDBACK LEARNING
                                 │
                                 ▼
                   MODEL TELEMETRY & DRIFT (PSI)
```

---

## 🧩 2. Six Core AI Modules

| Module | Purpose | Real Implementation |
| :--- | :--- | :--- |
| **1. 🎯 Customer Propensity Engine** | Pre-contact prediction | Random Forest Classifier trained with `class_weight='balanced'`. Computes pre-contact subscription probability and Opportunity Score ($0–100$). |
| **2. 🚀 Campaign Optimizer** | Capacity-constrained triage | Solves calling capacity limits (e.g. 2,000 slots). Ranks entire lead pool, bins into **Tier A** (🔥 Contact First), **Tier B** (🟡 Next), **Tier C** (⚪ Nurture), **Tier D** (⚫ Suppress), and generates expected conversion yield & **3.8x efficiency lift**. |
| **3. 🧠 Explainable AI Signals** | Transparent model interpretation | Directional predictive associations (e.g., Previous Campaign Success $+$, No Housing Debt $+$, High Balance $+$, Active Personal Loan $-$) with explicit non-causal disclaimer. |
| **4. 💡 Next Best Action** | Operational decision rules | Deterministic business rules converting ML scores into banking actions: Senior RM outreach ($\ge 65$), Digital Nudge ($40-64$), or Outbound Call Suppression ($<40$). |
| **5. 🔄 Campaign Feedback Intelligence** | Closed-loop evaluation | Compares predicted positive calls against actual subscriptions ($579$ TP captured, $6,501$ non-subscribers avoided, saving $71.9\%$ of wasted cold call agent hours). |
| **6. 🛡️ Model Health & Drift** | Telemetry & production readiness | Live monitoring of data quality ($0$ nulls, $0$ duplicates), Population Stability Index (PSI = $0.024$, healthy), score distribution, and Leakage Guard status. |

---

## 🛡️ 3. Pre-Contact Leakage Guard Contract

The model predicts strictly **before contact initiation**. In-campaign and post-contact variables are excluded:

| Excluded Feature | Reason for Exclusion | Leakage Mechanism |
| :--- | :--- | :--- |
| `duration` | Call duration in seconds | Unknown before the call is answered. High duration correlates with subscription but is a post-contact outcome. |
| `contact` | Communication channel | Assigned during the current outreach action. |
| `day`, `month` | Contact day/month | Scheduling attributes of current outreach. |
| `campaign` | In-campaign contact count | Dynamic counter of current campaign cycle. |

### Active Pre-Contact Features (11 Total):
* **Demographics (4):** `age`, `job`, `marital`, `education`
* **Financial Profile (4):** `balance`, `default`, `housing`, `loan`
* **Historical Prior Campaign Context (3):** `poutcome`, `pdays`, `previous`

---

## 📊 4. Real Model Evaluation Benchmarks

*Evaluated on isolated 20% Unseen Test Set (9,043 records) from UCI Bank Marketing dataset:*

| Metric | Logistic Regression (Baseline) | Random Forest (Selected Model) | Advantage |
| :--- | :--- | :--- | :--- |
| **Accuracy** | 70.89% | **78.29%** | $+7.40\%$ |
| **Precision** | 22.34% | **28.07%** | $+5.73\%$ |
| **Recall** | 60.17% | **54.73%** | High Sensitivity |
| **Positive F1-Score** | 0.3259 | **0.3710** | $+13.8\%$ Relative Lift |
| **ROC-AUC** | 0.7184 | **0.7348** | $+0.016$ |

### Confusion Matrix (Test Set Partition: 9,043 Cases):
* **True Negatives (TN):** $6,501$ non-subscribers successfully filtered out.
* **False Positives (FP):** $1,484$ calls made that did not subscribe (~5 min call cost).
* **False Negatives (FN):** $479$ missed opportunities (minimized by balanced class weighting).
* **True Positives (TP):** $579$ deposit subscribers captured.

---

## 🗄️ 5. SQLite Persistence Engine (`data/smartbank.db`)

All application activity is persisted in SQLite across 6 structured tables:

1. **`users`**: Demo accounts (`analyst@smartbank.ai` / `demo123`, `admin@smartbank.ai` / `admin123`).
2. **`customers`**: Customer lead directory with demographic and financial attributes.
3. **`assessments`**: Logged prediction events with Opportunity Scores, priorities, and predictive signals.
4. **`campaign_optimizer_runs`**: Capacity optimization benchmarks and simulation runs.
5. **`campaign_feedback`**: Ground-truth historical feedback comparisons.
6. **`model_telemetry`**: Model health snapshots, PSI drift score, and prediction distribution.

---

## 🚀 6. Running Locally

### Step 1: Clone & Setup Environment
```powershell
git clone https://github.com/smitha2422/SmartBank-ai.git
cd SmartBank-ai

# Create & activate virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Train Model & Seed Database
```powershell
# 1. Run leakage-safe training pipeline
python src/train.py

# 2. Seed SQLite database with verified leads & benchmarks
python src/seed_db.py
```

### Step 3: Start Application Server
```powershell
uvicorn backend.app:app --reload --port 8000
```
Open **`http://127.0.0.1:8000`** in your browser.

> **Demo Login Credentials:**
> - **Campaign Analyst:** `analyst@smartbank.ai` / `demo123`
> - **Administrator:** `admin@smartbank.ai` / `admin123`

---

## 📁 7. Repository Structure

```
SmartBank-AI/
├── backend/
│   ├── app.py                     # FastAPI REST API & Static Frontend Mount
│   └── database.py                # SQLite Persistence Layer & CRUD Handlers
├── data/
│   ├── bank-full.csv              # UCI Bank Marketing Dataset (45,211 rows)
│   └── smartbank.db               # SQLite 3 Database Engine
├── frontend/
│   ├── index.html                 # Complete PWA & Web Application UI
│   ├── styles.css                 # Dark Fintech Enterprise Design System
│   ├── app.js                     # Master Client Routing & State Controller
│   ├── manifest.json              # Web App Manifest
│   └── sw.js                      # Service Worker for Offline Resilience
├── models/
│   └── best_pipeline.joblib       # Trained Random Forest Preprocessor + Model
├── notebooks/
│   └── bank_marketing_analysis.ipynb # End-to-end EDA, Training & Evaluation Notebook
├── outputs/
│   ├── metrics.json               # Real Evaluation Benchmark Metrics
│   ├── eda_summary.json           # Dataset Statistics Summary
│   ├── feature_importance.json    # Ranked Predictive Signals
│   ├── confusion_matrix.png       # Test Partition Confusion Matrix Plot
│   ├── model_comparison.png       # LR vs RF Metric Comparison Plot
│   └── roc_curve.png              # ROC Curve Plot
├── src/
│   ├── train.py                   # Reproducible ML Training Pipeline
│   └── seed_db.py                 # SQLite Database Seeder Script
├── requirements.txt               # Python Dependencies
└── README.md                      # Comprehensive Project Documentation
```

---

## 🎤 8. Gupio Interview Presentation Summary

1. **The Business Problem:** Indiscriminate bank cold calling wastes agent hours and causes customer fatigue. SmartBank AI predicts subscription likelihood before contact to optimize limited calling capacity.
2. **Leakage Guard:** We strictly excluded `duration` and 4 other in-campaign attributes because call length is physically impossible to know before customer pickup.
3. **Class Imbalance:** Only 11.7% of customers subscribe. Naive models get 88.3% accuracy but zero business value. We trained a cost-sensitive Random Forest with `class_weight='balanced'` and evaluated on F1 and ROC-AUC.
4. **Campaign Optimizer:** Rather than stopping at abstract probabilities, the platform ranks leads against a capacity constraint (e.g. 2,000 calls), delivering a **3.8x efficiency lift** over random calling.
5. **Responsible AI:** Feature weights are presented as **predictive associations**, not causal levers, reinforced with an embedded SQLite audit trail.
