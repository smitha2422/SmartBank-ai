# SmartBank AI — Pre-Contact Term Deposit Subscription Prediction & Campaign Intelligence

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.5%2B-F7931E.svg)](https://scikit-learn.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An enterprise-grade, leakage-safe machine learning system designed to estimate bank customer term deposit subscription likelihood **strictly before** initiating direct marketing outreach.

---

## 1. Project Overview
In retail banking, outbound direct marketing campaigns (telephone outreach) represent a significant operational cost. Contacting every customer indiscriminately leads to customer fatigue, low conversion rates, and wasted agent hours. 

**SmartBank AI** transforms raw bank customer demographic and historical interaction data into an actionable **Opportunity Score (0–100)** and triage **Campaign Priority (HIGH / MEDIUM / LOW)** before any call is made.

---

## 2. Business Problem & Objective
* **Core Question:** *Can we identify customers who are most likely to subscribe to a term deposit before picking up the phone?*
* **Target Variable:** Binary deposit subscription (`y`: `yes` vs. `no`).
* **Objective:** Maximize positive-class detection (Recall & F1-Score) and ranking ability (ROC-AUC) within a strict pre-contact boundary, enabling relationship managers to prioritize high-value conversations.

---

## 3. Dataset Specification
* **Source:** UCI Bank Marketing Dataset (ID: 222).
* **Instance Count:** 45,211 rows.
* **Feature Count:** 17 columns (semicolon-delimited `bank-full.csv`).
* **Target Distribution:** 
  * `no`: 39,922 records (88.30%)
  * `yes`: 5,289 records (11.70%) — *Significant Class Imbalance*

---

## 4. Prediction Point Definition
The system enforces a clear operational boundary:
$$\text{Prediction Point} \equiv \text{Immediately prior to the current campaign contact}$$

All information that only becomes observable during or after the telephone conversation is unavailable at inference time.

---

## 5. Strict Leakage Prevention
To guarantee that the model is production-realistic, the following features were **strictly excluded**:

| Excluded Feature | Reason for Exclusion | Leakage Mechanism |
| :--- | :--- | :--- |
| `duration` | Call duration in seconds | Unknown before the call is answered. A long duration heavily correlates with subscription but is a post-contact outcome. |
| `contact` | Contact communication type | Relates directly to the current outreach action. |
| `day` | Day of the month | Specific to current campaign timing. |
| `month` | Last contact month | Specific to current campaign timing. |
| `campaign` | Number of contacts in current campaign | Dynamic attribute of current outreach cycle. |
| `pdays` | Days since previous contact | Excluded or sanitized to avoid post-campaign leakage. |

### Retained Pre-Contact Features (10 Total):
* **Numerical (3):** `age`, `balance`, `previous`
* **Categorical (7):** `job`, `marital`, `education`, `default`, `housing`, `loan`, `poutcome`

---

## 6. Exploratory Data Analysis (EDA)
* **Missing Values (NaN):** 0 null entries across all 45,211 records.
* **Duplicate Rows:** 0 duplicate rows detected.
* **Class Ratio:** ~7.5 to 1 ratio (`no` to `yes`).
* **Key Observations:**
  * Customers with prior campaign `success` show markedly higher subscription probability.
  * Absence of a housing loan (`housing = 'no'`) is positively associated with subscription likelihood.
  * Higher average balance (`balance > €2,000`) and senior/retired demographic profiles show elevated deposit affinity.

---

## 7. Preprocessing & Leakage-Safe Pipeline Architecture
Preprocessing is encapsulated inside an isolated `sklearn.pipeline.Pipeline` with `ColumnTransformer`:
* **Numerical Pipeline:** `SimpleImputer(strategy='median')` $\rightarrow$ `StandardScaler()`
* **Categorical Pipeline:** `SimpleImputer(strategy='most_frequent')` $\rightarrow$ `OneHotEncoder(handle_unknown='ignore', sparse_output=False)`

> **Zero Leakage Rule:** Preprocessor transformations are **fitted exclusively on the training split** and applied onto validation and unseen test sets without refitting encoders or scalers.

---

## 8. Class Imbalance Handling
Because the positive class (`yes`) constitutes only 11.70% of the dataset:
* Naive models predicting `no` for all cases achieve **88.30% accuracy** while offering **0% business utility**.
* We incorporated cost-sensitive learning via `class_weight='balanced'` in both baseline and ensemble classifiers.
* Evaluation prioritizes **Precision, Recall, F1-Score, and ROC-AUC** over raw Accuracy.

---

## 9. 3-Way Stratified Data Splitting Strategy
```
45,211 Total Records
 │
 ├── Development Set (80% — 36,168 records)
 │    ├── Training Partition (64% — 28,934 records) [Fit Preprocessor & Models]
 │    └── Validation Partition (16% — 7,234 records) [Model Selection Benchmark]
 │
 └── Final Unseen Test Set (20% — 9,043 records) [Strictly Isolated from Model Selection]
```

---

## 10. Model Comparison & Selection

| Metric | Logistic Regression (Baseline) | Random Forest (Ensemble) | Selected Final Model |
| :--- | :---: | :---: | :---: |
| **Validation Accuracy** | 70.90% | **78.45%** | 🏆 **Random Forest** |
| **Positive Precision** | 22.31% | **28.61%** | 🏆 **Random Forest** |
| **Positive Recall** | **59.93%** | 56.38% | — |
| **F1-Score** | 0.3251 | **0.3796** | 🏆 **Random Forest (+0.0545)** |
| **ROC-AUC** | 0.7183 | **0.7393** | 🏆 **Random Forest (+0.0210)** |

### Selection Rationale:
* **Random Forest** demonstrated superior discrimination capability (ROC-AUC: 0.7393 vs 0.7183) and a significantly higher F1-score (+16.7% relative improvement), striking the optimal precision-recall balance for campaign resource allocation.

---

## 11. Final Unseen Test Evaluation
After refitting the winning Random Forest pipeline on the full 80% Development dataset, it was evaluated once on the isolated 20% Unseen Test Set (9,043 rows):

* **Test Accuracy:** 77.86%
* **Test Precision:** 27.37%
* **Test Recall:** 53.97%
* **Test F1-Score:** 0.3632
* **Test ROC-AUC:** **0.7288**

### Confusion Matrix (Test Set):
```
                 Predicted NO    Predicted YES
 Actual NO          6,470            1,515
 Actual YES           487              571
```

---

## 12. Feature Interpretability & Predictive Signals
Extracting top predictive signals from the Random Forest model:

1. **`age`** (Importance: `0.1526`)
2. **`balance`** (Importance: `0.1462`)
3. **`poutcome_success`** (Importance: `0.1447`)
4. **`previous`** (Importance: `0.0922`)
5. **`housing_no`** (Importance: `0.0737`)

> **Scientific Disclaimer:** Feature importance reflects mathematical association within the predictive pipeline. It indicates statistical predictive correlation rather than causal mechanisms.

---

## 13. System Architecture & File Structure
```
SmartBank-AI/
│
├── backend/
│   └── app.py                      # FastAPI inference & dashboard telemetry service
│
├── data/
│   └── bank-full.csv               # UCI Bank Marketing dataset (45,211 rows)
│
├── frontend/
│   ├── index.html                  # Interactive modern fintech interface
│   ├── styles.css                  # Dark luxury glassmorphism design system
│   └── app.js                      # Dynamic client logic, API hooks & fallback simulation
│
├── models/
│   └── best_pipeline.joblib        # Fitted ColumnTransformer + Random Forest pipeline
│
├── notebooks/
│   └── bank_marketing_analysis.ipynb # EDA & experimental analysis notebook
│
├── outputs/
│   ├── metrics.json                # Complete validation & test evaluation metrics
│   ├── eda_summary.json            # Dataset shape, missing values & target distribution
│   ├── feature_importance.json     # Ranked predictive signals & coefficients
│   ├── sample_test_records.csv     # Sample evaluation inference outputs
│   ├── confusion_matrix.png        # Seaborn confusion matrix visualization
│   ├── model_comparison.png        # Bar chart comparison of models
│   └── roc_curve.png               # ROC curve with AUC score
│
├── src/
│   └── train.py                    # End-to-end reproducible training script
│
├── .gitignore                      # Safeguards virtual environment, secrets & cache
├── README.md                       # Comprehensive project documentation
└── requirements.txt                # Pinned production dependencies
```

---

## 14. Installation & Setup

### Step 1: Clone Repository
```bash
git clone https://github.com/smitha2422/SmartBank-ai.git
cd SmartBank-ai
```

### Step 2: Create & Activate Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 15. Execution Instructions

### A. Run End-to-End Machine Learning Pipeline
```bash
python src/train.py
```
*Generates model artifacts in `models/` and visual metrics in `outputs/`.*

### B. Start FastAPI Inference Backend
```bash
uvicorn backend.app:app --reload --port 8000
```
* Interactive API Documentation (Swagger UI): `http://127.0.0.1:8000/docs`
* Health Check: `http://127.0.0.1:8000/health`
* Dashboard Telemetry: `http://127.0.0.1:8000/dashboard`

### C. Launch Interactive Frontend Dashboard
```bash
# In a new terminal window (with .venv active):
python -m http.server 5500 -d frontend
```
* Open your browser at: **`http://127.0.0.1:5500`**

---

## 16. API Specification (`POST /predict`)

### Example Request Body:
```json
{
  "age": 58,
  "job": "management",
  "marital": "married",
  "education": "tertiary",
  "default": "no",
  "balance": 3250.0,
  "housing": "no",
  "loan": "no",
  "poutcome": "success",
  "previous": 2
}
```

### Example Response:
```json
{
  "probability": 0.724,
  "opportunity_score": 72,
  "campaign_priority": "HIGH",
  "prediction_label": "Likely to Subscribe",
  "recommendation": "High engagement opportunity: Assign to senior relationship manager with premium deposit terms.",
  "predictive_signals": [
    { "factor": "Previous Campaign Success", "impact": "Strong Positive", "type": "positive" },
    { "factor": "No Housing Loan Obligation", "impact": "Positive", "type": "positive" },
    { "factor": "Healthy Account Balance (>€2,000)", "impact": "Positive", "type": "positive" }
  ],
  "disclaimer": "The Opportunity Score translates predictive likelihood into a campaign prioritization signal. It represents statistical association and does not guarantee subscription."
}
```

---

## 17. Assumptions & Limitations
1. **Historical Static Dataset:** Data originates from previous Portuguese banking campaigns; macroeconomic changes (interest rates, inflation) alter baseline subscription propensity.
2. **Missing In-Session Context:** Excluded duration prevents knowing if customer engaged in deep dialogue, strictly conforming to the pre-contact constraint.
3. **Correlation vs. Causation:** Feature importance highlights predictive patterns, not direct levers to induce deposit opening.

---

## 18. Future Improvements & Roadmap
* **Phase 2 — Explainability & Tuning:** SHAP (SHapley Additive exPlanations) values for individual prediction explainability and Bayesian Hyperparameter optimization.
* **Phase 3 — Operational Integration:** Containerization with Docker and automated CRM webhook trigger integration.
* **Phase 4 — MLOps & Continuous Learning:** Automated data drift monitoring, PSI (Population Stability Index) tracking, and live A/B campaign uplift testing.

---
**Author:** Smitha Srinivas  
**Repository:** [https://github.com/smitha2422/SmartBank-ai](https://github.com/smitha2422/SmartBank-ai)
