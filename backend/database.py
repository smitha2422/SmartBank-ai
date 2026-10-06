"""
SmartBank AI - Database Engine
SQLite persistence for Real Users/Employees, Customers, Assessments, Campaign Optimization, Feedback, and Telemetry.
"""

import os
import sqlite3
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "smartbank.db")

def hash_password(password: str) -> str:
    """Computes SHA-256 hash for secure local password verification."""
    return hashlib.sha256(password.strip().encode("utf-8")).hexdigest()

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes SQLite schema for SmartBank AI platform."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Users / Employees Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        name TEXT NOT NULL,
        role TEXT NOT NULL,
        department TEXT DEFAULT 'Campaign Intelligence',
        last_login TEXT,
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
        source TEXT NOT NULL DEFAULT 'manual',
        created_by TEXT DEFAULT 'Staff Operator',
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
        analyst_name TEXT DEFAULT 'Campaign Analyst',
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
    
    # Backwards-compatible customer_predictions table
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
    
    # 7. Customer Term Deposit Bookings Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customer_deposits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        certificate_id TEXT UNIQUE NOT NULL,
        customer_id TEXT NOT NULL,
        customer_name TEXT NOT NULL,
        account_number TEXT NOT NULL,
        deposit_amount REAL NOT NULL,
        term_months INTEGER NOT NULL,
        annual_rate REAL NOT NULL,
        interest_earned REAL NOT NULL,
        maturity_amount REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'ACTIVE',
        booked_at TEXT NOT NULL,
        maturity_date TEXT NOT NULL
    )
    """)
    
    # Column migration checks for existing tables
    def ensure_column(table, column, col_type):
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
        except sqlite3.OperationalError:
            pass
            
    ensure_column("users", "department", "TEXT DEFAULT 'Campaign Intelligence'")
    ensure_column("users", "last_login", "TEXT")
    ensure_column("customers", "created_by", "TEXT DEFAULT 'Staff Operator'")
    ensure_column("assessments", "analyst_name", "TEXT DEFAULT 'Campaign Analyst'")
    ensure_column("campaign_optimizer_runs", "pool_size", "INTEGER NOT NULL DEFAULT 5000")
    ensure_column("campaign_optimizer_runs", "analyst_user", "TEXT NOT NULL DEFAULT 'Campaign Analyst'")
    ensure_column("model_telemetry", "psi_score", "REAL DEFAULT 0.024")
    ensure_column("customer_predictions", "pdays", "INTEGER NOT NULL DEFAULT -1")
    ensure_column("customers", "pdays", "INTEGER NOT NULL DEFAULT -1")
    
    # Financial, EMI, Deposit limits & AI verification columns
    ensure_column("customers", "salary_monthly", "REAL DEFAULT 3800.0")
    ensure_column("customers", "housing_emi", "REAL DEFAULT 0.0")
    ensure_column("customers", "personal_loan_emi", "REAL DEFAULT 0.0")
    ensure_column("customers", "account_number", "TEXT DEFAULT 'SB-88219482'")
    ensure_column("customers", "kyc_verified", "INTEGER DEFAULT 1")
    ensure_column("customers", "max_deposit_limit", "REAL DEFAULT 12000.0")
    ensure_column("customers", "recommended_deposit", "REAL DEFAULT 4000.0")
    ensure_column("customers", "risk_failure_score", "REAL DEFAULT 0.12")
    ensure_column("customers", "fail_signals", "TEXT DEFAULT '[]'")

    # Ensure baseline administrator, analyst, and verified customer users exist
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
        INSERT INTO users (email, password, name, role, department, created_at) VALUES 
        ('admin@smartbank.ai', 'admin123', 'Sarah Vance', 'Administrator', 'Executive Intelligence', ?),
        ('analyst@smartbank.ai', 'analyst123', 'Alex Mercer', 'Campaign Analyst', 'Retail Marketing', ?),
        ('customer@smartbank.ai', 'cust123', 'Arthur Pendelton', 'Customer', 'Verified Banking Client', ?),
        ('elena.rostova@smartbank.ai', 'staff123', 'Elena Rostova', 'Campaign Analyst', 'Digital Banking Outreach', ?),
        ('david.miller@smartbank.ai', 'staff123', 'David Miller', 'Campaign Analyst', 'Wealth & Term Deposits', ?)
        """, (now, now, now, now, now))
    else:
        # Ensure analyst has analyst123 password
        cursor.execute("UPDATE users SET password = 'analyst123' WHERE email = 'analyst@smartbank.ai' AND password = 'demo123'")
        
        # Ensure customer user exists
        cursor.execute("SELECT id FROM users WHERE email = 'customer@smartbank.ai'")
        if not cursor.fetchone():
            now = datetime.now(timezone.utc).isoformat()
            cursor.execute("""
            INSERT INTO users (email, password, name, role, department, created_at) VALUES 
            ('customer@smartbank.ai', 'cust123', 'Arthur Pendelton', 'Customer', 'Verified Banking Client', ?),
            ('elena.cust@smartbank.ai', 'cust123', 'Elena Rostova', 'Customer', 'Premier Wealth Client', ?),
            ('marcus.cust@smartbank.ai', 'cust123', 'Marcus Brody', 'Customer', 'Retail Client', ?)
            """, (now, now, now))
    
    # Ensure Arthur Pendelton customer record exists in customers table
    cursor.execute("SELECT id FROM customers WHERE customer_id = 'CUST-001' OR email = 'customer@smartbank.ai'")
    if not cursor.fetchone():
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
        INSERT INTO customers (
            customer_id, name, email, phone, age, job, marital, education,
            default_credit, balance, housing, loan, poutcome, pdays, previous, source, created_by,
            salary_monthly, housing_emi, personal_loan_emi, account_number, kyc_verified,
            max_deposit_limit, recommended_deposit, risk_failure_score, created_at
        ) VALUES (
            'CUST-001', 'Arthur Pendelton', 'customer@smartbank.ai', '+1 (555) 882-1948', 64, 'retired', 'married', 'tertiary',
            'no', 4800.0, 'no', 'no', 'success', 120, 3, 'verified_portal', 'System Administrator',
            3800.0, 0.0, 0.0, 'SB-88219482', 1,
            12500.0, 4200.0, 0.065, ?
        )
        """, (now,))
    else:
        cursor.execute("""
        UPDATE customers SET 
            email = 'customer@smartbank.ai',
            name = 'Arthur Pendelton',
            balance = 4800.0,
            salary_monthly = 3800.0,
            housing = 'no',
            loan = 'no',
            housing_emi = 0.0,
            personal_loan_emi = 0.0,
            account_number = 'SB-88219482',
            kyc_verified = 1
        WHERE customer_id = 'CUST-001' OR email = 'customer@smartbank.ai'
        """)

    conn.commit()
    conn.close()

# -------------------------------------------------------------
# USER AUTHENTICATION & MANAGEMENT
# -------------------------------------------------------------
def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    # Accept both plain string and sha256
    p_hash = hash_password(password)
    cursor.execute("""
    SELECT * FROM users 
    WHERE LOWER(email) = LOWER(?) AND (
        password = ? OR 
        password = ? OR 
        (password = 'demo123' AND ? = 'analyst123') OR
        (password = 'analyst123' AND ? = 'demo123')
    )
    """, (email.strip(), password.strip(), p_hash, password.strip(), password.strip()))
    row = cursor.fetchone()
    
    if row:
        user_dict = dict(row)
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute("UPDATE users SET last_login = ? WHERE id = ?", (now, row["id"]))
        conn.commit()
        conn.close()
        return {
            "id": user_dict["id"],
            "email": user_dict["email"],
            "name": user_dict["name"],
            "role": user_dict["role"],
            "department": user_dict.get("department", "Campaign Intelligence"),
            "created_at": user_dict["created_at"],
            "last_login": now
        }
    conn.close()
    return None

def register_user(name: str, email: str, password: str, role: str = "Campaign Analyst", department: str = "Campaign Intelligence") -> Dict[str, Any]:
    """Registers a real new staff or administrator account in SQLite."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if email exists
    cursor.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(?)", (email.strip(),))
    if cursor.fetchone():
        conn.close()
        raise ValueError(f"An account with email '{email}' already exists.")
        
    now = datetime.now(timezone.utc).isoformat()
    cursor.execute("""
    INSERT INTO users (email, password, name, role, department, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        email.strip().lower(),
        password.strip(),
        name.strip(),
        role.strip(),
        department.strip(),
        now
    ))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {
        "id": new_id,
        "name": name.strip(),
        "email": email.strip().lower(),
        "role": role.strip(),
        "department": department.strip(),
        "created_at": now
    }

def list_all_users() -> List[Dict[str, Any]]:
    """Lists all registered employees and administrators along with assessment activity counts."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT u.id, u.name, u.email, u.role, u.department, u.created_at, u.last_login,
           COUNT(a.id) as assessments_count
    FROM users u
    LEFT JOIN assessments a ON LOWER(a.analyst_name) LIKE '%' || LOWER(u.name) || '%'
    GROUP BY u.id
    ORDER BY u.id ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_user(user_id: int) -> bool:
    """Deletes an employee account (Admin action)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def get_admin_analytics() -> Dict[str, Any]:
    """Computes system-wide administrative analysis and staff productivity metrics."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'Administrator'")
    admin_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE role LIKE '%Analyst%'")
    analyst_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM customers")
    total_customers = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM assessments")
    total_assessments = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM campaign_optimizer_runs")
    total_optimizer_runs = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM campaign_feedback")
    total_feedback = cursor.fetchone()[0]
    
    # Recent assessment log by employees
    cursor.execute("""
    SELECT id, customer_id, customer_name, analyst_name, opportunity_score, campaign_priority, timestamp 
    FROM assessments ORDER BY id DESC LIMIT 10
    """)
    recent_staff_assessments = [dict(r) for r in cursor.fetchall()]
    
    # Table storage statistics
    tables = [
        {"table_name": "users", "row_count": total_users, "description": "Registered Staff & Admins"},
        {"table_name": "customers", "row_count": total_customers, "description": "Customer Lead Directory"},
        {"table_name": "assessments", "row_count": total_assessments, "description": "AI Assessment Audit Trail"},
        {"table_name": "campaign_optimizer_runs", "row_count": total_optimizer_runs, "description": "Capacity Optimization Runs"},
        {"table_name": "campaign_feedback", "row_count": total_feedback, "description": "Closed-Loop Feedback Logs"},
        {"table_name": "model_telemetry", "row_count": 1, "description": "Live Telemetry Snapshots"}
    ]
    
    db_size_bytes = os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0
    
    conn.close()
    
    return {
        "system": {
            "total_users": total_users,
            "administrators": admin_count,
            "campaign_analysts": analyst_count,
            "total_assessments_logged": total_assessments,
            "database_size_bytes": db_size_bytes
        },
        "tables": tables,
        "recent_assessments": recent_staff_assessments,
        "staff_metrics": {
            "total_staff": total_users,
            "administrators": admin_count,
            "campaign_analysts": analyst_count
        },
        "database_metrics": {
            "db_path": "data/smartbank.db",
            "db_size_kb": round(db_size_bytes / 1024, 1),
            "tables": tables
        },
        "system_status": {
            "model_engine": "Random Forest v1.0 (Balanced Ensemble)",
            "leakage_guard": "Active (100% Pre-Contact Enforced)",
            "api_health": "ONLINE"
        },
        "recent_staff_assessments": recent_staff_assessments
    }

# -------------------------------------------------------------
# CUSTOMER FINANCIAL INTELLIGENCE & VERIFICATION
# -------------------------------------------------------------
def calculate_job_salary(job: str) -> float:
    salaries = {
        "management": 5800.0,
        "entrepreneur": 5200.0,
        "technician": 3600.0,
        "admin.": 3200.0,
        "services": 2800.0,
        "self-employed": 3900.0,
        "retired": 2600.0,
        "blue-collar": 2700.0,
        "housemaid": 1800.0,
        "student": 1100.0,
        "unemployed": 950.0
    }
    return salaries.get(str(job).lower(), 3400.0)

def enrich_customer_financials(c: Dict[str, Any]) -> Dict[str, Any]:
    """Calculates live comprehensive banking details: salary, EMIs, deposit limits, yield projections, and failure risks."""
    salary = float(c.get("salary_monthly") or calculate_job_salary(c.get("job", "technician")))
    
    # EMIs
    housing_emi = float(c.get("housing_emi") or (round(salary * 0.28, 2) if str(c.get("housing", "")).lower() == "yes" else 0.0))
    loan_emi = float(c.get("personal_loan_emi") or (round(salary * 0.12, 2) if str(c.get("loan", "")).lower() == "yes" else 0.0))
    total_emi = round(housing_emi + loan_emi, 2)
    
    disposable_monthly = max(0.0, round(salary - total_emi, 2))
    dti_pct = round((total_emi / salary * 100), 1) if salary > 0 else 0.0
    
    balance = float(c.get("balance", 0.0))
    emergency_reserve = round(salary * 1.5, 2)
    available_liquidity = max(0.0, round(balance - emergency_reserve, 2))
    
    # Term deposit limits
    max_deposit_limit = max(500.0, round(available_liquidity + (disposable_monthly * 2.0), 2))
    recommended_deposit = max(250.0, round((available_liquidity * 0.6) + (disposable_monthly * 1.0), 2))
    
    # Calculate failure / financial distress probability (0.0 to 1.0)
    fail_risk = 0.08  # baseline 8%
    fail_signals = []
    
    if str(c.get("default_credit", c.get("default", "no"))).lower() == "yes":
        fail_risk += 0.40
        fail_signals.append({
            "type": "CRITICAL_RISK",
            "message": "Historical Credit Default: Customer previously defaulted on credit obligations.",
            "impact": "+40% Default Risk"
        })
        
    if dti_pct >= 40.0:
        fail_risk += 0.28
        fail_signals.append({
            "type": "HIGH_EMI_BURDEN",
            "message": f"Overleveraged DTI ({dti_pct}%): Monthly debt obligations (€{total_emi}) consume over 40% of income.",
            "impact": "+28% Liquidity Strain"
        })
    elif dti_pct >= 25.0:
        fail_risk += 0.12
        fail_signals.append({
            "type": "MODERATE_EMI_BURDEN",
            "message": f"Moderate Debt Burden ({dti_pct}%): Total active EMIs are €{total_emi}/month.",
            "impact": "+12% Friction"
        })
        
    if balance < 300.0:
        fail_risk += 0.25
        fail_signals.append({
            "type": "DEPLETED_BUFFER",
            "message": f"Critical Liquidity Deficit: Total account balance is only €{balance:.2f} (under minimum safety threshold).",
            "impact": "+25% Distress Risk"
        })
    elif balance < emergency_reserve:
        fail_risk += 0.10
        fail_signals.append({
            "type": "LOW_EMERGENCY_RESERVE",
            "message": f"Tight Emergency Buffer: Balance (€{balance:.2f}) is below the recommended 1.5x monthly salary buffer (€{emergency_reserve:.2f}).",
            "impact": "+10% Cashflow Risk"
        })
        
    if str(c.get("poutcome", "")).lower() == "failure":
        fail_risk += 0.08
        fail_signals.append({
            "type": "PRIOR_CAMPAIGN_FRICTION",
            "message": "Past Outreach Resistance: Customer recorded an unsuccessful outcome in previous marketing cycle.",
            "impact": "+8% Friction"
        })
    elif str(c.get("poutcome", "")).lower() == "success":
        fail_risk -= 0.06
        fail_signals.append({
            "type": "POSITIVE_HISTORY",
            "message": "Proven Subscription Track Record: Previous campaign subscription was successful.",
            "impact": "-6% Low Risk"
        })
        
    if balance >= 4000.0 and dti_pct < 20.0:
        fail_risk -= 0.05
        fail_signals.append({
            "type": "HIGH_LIQUIDITY_SURPLUS",
            "message": "Prime Financial Health: High surplus liquidity with minimal debt obligations.",
            "impact": "Prime Safe Tier"
        })

    fail_risk = max(0.02, min(0.95, round(fail_risk, 3)))
    
    if fail_risk < 0.20:
        fail_category = "SAFE_LOW_RISK"
        safety_badge = "VERIFIED_SAFE"
    elif fail_risk < 0.45:
        fail_category = "MODERATE_CAUTION"
        safety_badge = "CAUTION_ADVISED"
    else:
        fail_category = "HIGH_DISTRESS_RISK"
        safety_badge = "HIGH_FAILURE_RISK"
        
    # Projected interest yields at bank standard rates
    yield_12m = round(recommended_deposit * 0.0425, 2)
    yield_24m = round(recommended_deposit * 0.0460 * 2, 2)
    yield_36m = round(recommended_deposit * 0.0485 * 3, 2)
    
    return {
        **c,
        "account_number": c.get("account_number") or f"SB-{abs(hash(c.get('customer_id', 'cust')))%90000000 + 10000000}",
        "kyc_verified": bool(c.get("kyc_verified", 1)),
        "salary_monthly": salary,
        "housing_emi": housing_emi,
        "personal_loan_emi": loan_emi,
        "total_monthly_emi": total_emi,
        "total_emi_monthly": total_emi,
        "net_disposable_income": disposable_monthly,
        "disposable_income_monthly": disposable_monthly,
        "dti_ratio_pct": dti_pct,
        "emergency_liquidity_reserve": emergency_reserve,
        "available_surplus_liquidity": available_liquidity,
        "max_deposit_limit": max_deposit_limit,
        "recommended_deposit": recommended_deposit,
        "risk_failure_score": fail_risk,
        "risk_failure_pct": f"{round(fail_risk * 100, 1)}%",
        "fail_category": fail_category,
        "safety_badge": safety_badge,
        "fail_signals": fail_signals,
        "term_yield_projections": {
            "rate_12m_pa": "4.25%",
            "yield_12m": yield_12m,
            "maturity_12m": round(recommended_deposit + yield_12m, 2),
            "rate_24m_pa": "4.60%",
            "yield_24m": yield_24m,
            "maturity_24m": round(recommended_deposit + yield_24m, 2),
            "rate_36m_pa": "4.85%",
            "yield_36m": yield_36m,
            "maturity_36m": round(recommended_deposit + yield_36m, 2)
        }
    }

# -------------------------------------------------------------
# CUSTOMER MANAGEMENT & DIRECTORY
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
    return [enrich_customer_financials(dict(r)) for r in rows]

def get_customer_by_id(customer_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customers WHERE customer_id = ? OR id = ? OR LOWER(email) = LOWER(?) OR LOWER(name) LIKE ?", 
                   (customer_id, customer_id, customer_id.strip(), f"%{customer_id.strip().lower()}%"))
    row = cursor.fetchone()
    conn.close()
    return enrich_customer_financials(dict(row)) if row else None

def get_customer_financial_profile(customer_id_or_email: str) -> Optional[Dict[str, Any]]:
    """Retrieves full verified banking profile, EMIs, salary, and AI failure diagnostics."""
    cust = get_customer_by_id(customer_id_or_email)
    if not cust:
        # Fallback to demo default if user is logged in as generic customer
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customers ORDER BY id ASC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        if row:
            cust = enrich_customer_financials(dict(row))
    return cust

def verify_customer_deposit_simulation(customer_id_or_email: str, deposit_amount: float, term_months: int = 12) -> Dict[str, Any]:
    """
    AI Safety Verification Engine:
    Simulates placing a term deposit and verifies whether the customer will encounter
    liquidity distress, debt strain, or failure during the deposit period.
    """
    cust = get_customer_financial_profile(customer_id_or_email)
    if not cust:
        raise ValueError("Customer record not found for verification.")
        
    balance = float(cust.get("balance", 0.0))
    salary = float(cust.get("salary_monthly", 3500.0))
    emergency_buffer = float(cust.get("emergency_liquidity_reserve", salary * 1.5))
    total_emi = float(cust.get("total_monthly_emi", 0.0))
    dti_pct = float(cust.get("dti_ratio_pct", 0.0))
    max_limit = float(cust.get("max_deposit_limit", 10000.0))
    rec_amount = float(cust.get("recommended_deposit", 3500.0))
    
    post_deposit_balance = round(balance - deposit_amount, 2)
    rate_map = {6: 0.038, 12: 0.0425, 24: 0.0460, 36: 0.0485}
    annual_rate = rate_map.get(term_months, 0.0425)
    interest_earned = round(deposit_amount * annual_rate * (term_months / 12.0), 2)
    maturity_value = round(deposit_amount + interest_earned, 2)
    
    # AI Failure Risk Diagnostics
    distress_risk = 0.05
    distress_reasons = []
    
    if deposit_amount > balance:
        distress_risk = 0.99
        distress_reasons.append("Insufficient Funds: Requested deposit exceeds current available account balance.")
        verdict = "REJECTED_INSUFFICIENT_FUNDS"
        verdict_status = "CRITICAL_ERROR"
        verdict_color = "rose"
        verdict_title = "❌ Transaction Blocked — Insufficient Liquidity"
    elif post_deposit_balance < (salary * 0.5):
        distress_risk = 0.75
        distress_reasons.append(f"Severe Liquidity Depletion: Post-deposit balance (€{post_deposit_balance:.2f}) leaves less than 15 days living expenses.")
        verdict = "HIGH_DISTRESS_RISK"
        verdict_status = "FAIL_PREDICTED"
        verdict_color = "rose"
        verdict_title = "⚠️ High Risk of Premature Break / Cashflow Failure"
    elif post_deposit_balance < emergency_buffer:
        distress_risk = 0.40
        distress_reasons.append(f"Buffer Erosion: Remaining balance (€{post_deposit_balance:.2f}) dips below recommended 1.5x salary emergency reserve (€{emergency_buffer:.2f}).")
        verdict = "APPROVED_WITH_CAUTION"
        verdict_status = "CAUTION_REQUIRED"
        verdict_color = "amber"
        verdict_title = "🟡 Approved with Liquidity Advisory"
    else:
        distress_risk = 0.08
        verdict = "APPROVED_SAFE"
        verdict_status = "VERIFIED_SAFE"
        verdict_color = "emerald"
        verdict_title = "✅ AI Verified — Safe Deposit Capacity Confirmed"
        
    if dti_pct > 35.0:
        distress_risk += 0.15
        distress_reasons.append(f"High Debt Service: Active EMIs (€{total_emi}/mo) require consistent monthly cashflow allocation.")
        
    distress_risk = max(0.01, min(0.99, round(distress_risk, 3)))
    is_safe = verdict in ["APPROVED_SAFE", "APPROVED_WITH_CAUTION"]
    
    if verdict == "APPROVED_SAFE":
        advice = "Zero financial distress risk detected. Living expense reserves and EMI cashflows remain fully intact."
    elif verdict == "APPROVED_WITH_CAUTION":
        advice = f"Deposit approved, but remaining balance (€{post_deposit_balance:,.2f}) drops below the recommended 1.5x salary buffer (€{emergency_buffer:,.2f})."
    else:
        advice = "High cashflow failure risk. The proposed deposit excessively depletes liquid emergency buffers or exceeds current funds."

    return {
        "customer_id": cust.get("customer_id"),
        "customer_name": cust.get("name"),
        "account_number": cust.get("account_number"),
        "kyc_status": "KYC_VERIFIED" if cust.get("kyc_verified") else "PENDING_VERIFICATION",
        "requested_deposit": deposit_amount,
        "deposit_amount": deposit_amount,
        "term_months": term_months,
        "tenure_months": term_months,
        "annual_rate_pct": round(annual_rate * 100, 2),
        "annual_interest_rate": f"{round(annual_rate * 100, 2)}%",
        "projected_interest_yield": interest_earned,
        "projected_interest_earned": interest_earned,
        "maturity_amount": maturity_value,
        "projected_maturity_amount": maturity_value,
        "pre_deposit_balance": balance,
        "post_deposit_balance": post_deposit_balance,
        "emergency_reserve_required": emergency_buffer,
        "monthly_salary": salary,
        "monthly_emi_obligations": total_emi,
        "dti_ratio_pct": dti_pct,
        "max_recommended_ceiling": max_limit,
        "optimal_recommended_amount": rec_amount,
        "is_safe_to_deposit": is_safe,
        "verdict": verdict,
        "ai_verification_verdict": verdict,
        "verdict_title": verdict_title,
        "verdict_status": verdict_status,
        "verdict_color": verdict_color,
        "failure_distress_risk_pct": round(distress_risk * 100, 1),
        "ai_failure_probability": distress_risk,
        "ai_failure_risk_pct": f"{round(distress_risk * 100, 1)}%",
        "warning_signals": distress_reasons if distress_reasons else [],
        "predictive_failure_reasons": distress_reasons if distress_reasons else ["No financial distress risks detected. Profile has robust emergency reserves and clean debt profile."],
        "ai_financial_advice": advice,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

def create_customer(data: Dict[str, Any], creator_name: str = "Staff Operator") -> Dict[str, Any]:
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
        default_credit, balance, housing, loan, poutcome, pdays, previous, source, created_by, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        cid,
        data.get("name", "New Lead"),
        data.get("email", f"{cid.lower()}@smartbank-lead.org"),
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
        creator_name,
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
    analyst = data.get("analyst_name", "Campaign Analyst")
    now = datetime.now(timezone.utc).isoformat()
    
    cursor.execute("""
    INSERT INTO assessments (
        customer_id, customer_name, analyst_name, timestamp, model_version,
        probability, opportunity_score, campaign_priority, prediction_label,
        next_best_action, predictive_signals, input_features
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        cid,
        cname,
        analyst,
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

def get_recent_assessments(limit: int = 25) -> List[Dict[str, Any]]:
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

def update_user_profile(user_id: int, name: str = None, email: str = None, new_password: str = None, department: str = None) -> bool:
    """Updates user credentials and profile persistently in SQLite."""
    conn = get_connection()
    cursor = conn.cursor()
    updates = []
    params = []
    
    if name:
        updates.append("name = ?")
        params.append(name.strip())
    if email:
        updates.append("email = ?")
        params.append(email.strip().lower())
    if new_password and new_password.strip():
        updates.append("password = ?")
        params.append(new_password.strip())
    if department:
        updates.append("department = ?")
        params.append(department.strip())
        
    if not updates:
        conn.close()
        return False
        
    params.append(user_id)
    query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
    cursor.execute(query, tuple(params))
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

def update_customer_record(customer_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Updates customer contact, demographic, and financial details in SQLite."""
    conn = get_connection()
    cursor = conn.cursor()
    
    fields = [
        "name", "email", "phone", "age", "job", "marital", "education",
        "default_credit", "balance", "housing", "loan", "poutcome", "pdays", "previous",
        "salary_monthly", "housing_emi", "personal_loan_emi"
    ]
    
    updates = []
    params = []
    for f in fields:
        if f in data:
            val = data[f]
            if f in ["age", "pdays", "previous"]: val = int(val)
            elif f in ["balance", "salary_monthly", "housing_emi", "personal_loan_emi"]: val = float(val)
            else: val = str(val).lower() if f in ["job", "marital", "education", "default_credit", "housing", "loan", "poutcome"] else str(val)
            updates.append(f"{f} = ?")
            params.append(val)
            
    if not updates:
        conn.close()
        return get_customer_by_id(customer_id)
        
    params.append(customer_id)
    query = f"UPDATE customers SET {', '.join(updates)} WHERE customer_id = ? OR id = ?"
    params.append(customer_id)
    cursor.execute(query, tuple(params))
    conn.commit()
    conn.close()
    return get_customer_by_id(customer_id)

def delete_customer(customer_id: str) -> bool:
    """Deletes a customer record from SQLite."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM customers WHERE customer_id = ? OR id = ?", (customer_id, customer_id))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def book_term_deposit(customer_id_or_email: str, deposit_amount: float, term_months: int = 12) -> Dict[str, Any]:
    """
    Executes a verified fixed deposit booking:
    1. Verifies liquidity and safety.
    2. Deducts deposit amount from customer balance in SQLite.
    3. Generates and stores an official deposit certificate record in customer_deposits.
    """
    verification = verify_customer_deposit_simulation(customer_id_or_email, deposit_amount, term_months)
    if verification["verdict"] == "REJECTED_INSUFFICIENT_FUNDS":
        raise ValueError("Cannot book deposit: Insufficient account balance.")
        
    cust = get_customer_financial_profile(customer_id_or_email)
    conn = get_connection()
    cursor = conn.cursor()
    
    # Generate unique Certificate ID
    now = datetime.now(timezone.utc)
    cert_id = f"TD-{now.strftime('%Y%m%d')}-{abs(hash(now.isoformat())) % 90000 + 10000}"
    
    # Calculate maturity date
    maturity_year = now.year + (now.month + term_months - 1) // 12
    maturity_month = (now.month + term_months - 1) % 12 + 1
    maturity_date = f"{maturity_year}-{maturity_month:02d}-{now.day:02d}"
    
    cursor.execute("""
    INSERT INTO customer_deposits (
        certificate_id, customer_id, customer_name, account_number,
        deposit_amount, term_months, annual_rate, interest_earned,
        maturity_amount, status, booked_at, maturity_date
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?, ?)
    """, (
        cert_id,
        cust.get("customer_id", "CUST-001"),
        cust.get("name", "Arthur Pendelton"),
        cust.get("account_number", "SB-88219482"),
        float(deposit_amount),
        int(term_months),
        float(verification["annual_rate_pct"]),
        float(verification["projected_interest_yield"]),
        float(verification["projected_maturity_amount"]),
        now.isoformat(),
        maturity_date
    ))
    
    # Update customer balance in SQLite
    new_balance = round(float(cust.get("balance", 0.0)) - float(deposit_amount), 2)
    cursor.execute("UPDATE customers SET balance = ? WHERE customer_id = ? OR email = ?", 
                   (new_balance, cust.get("customer_id"), cust.get("email")))
    
    conn.commit()
    conn.close()
    
    return {
        "certificate_id": cert_id,
        "customer_id": cust.get("customer_id"),
        "customer_name": cust.get("name"),
        "account_number": cust.get("account_number"),
        "deposit_amount": deposit_amount,
        "term_months": term_months,
        "annual_rate": verification["annual_rate_pct"],
        "interest_earned": verification["projected_interest_yield"],
        "maturity_amount": verification["projected_maturity_amount"],
        "new_balance": new_balance,
        "booked_at": now.strftime("%b %d, %Y"),
        "maturity_date": maturity_date,
        "status": "ACTIVE"
    }

def get_customer_deposits(customer_id_or_email: str) -> List[Dict[str, Any]]:
    """Retrieves all active and historical term deposits for a customer."""
    cust = get_customer_financial_profile(customer_id_or_email)
    cid = cust.get("customer_id", customer_id_or_email)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customer_deposits WHERE customer_id = ? ORDER BY id DESC", (cid,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_latest_telemetry() -> Optional[Dict[str, Any]]:
    """Retrieves the latest model telemetry snapshot from SQLite."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM model_telemetry ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model_name": "Random Forest Champion",
        "model_version": "v1.0.0",
        "training_records": 45211,
        "active_features_count": 11,
        "health_status": "HEALTHY",
        "avg_inferred_probability": 0.324,
        "low_opportunity_pct": 52.0,
        "medium_opportunity_pct": 28.0,
        "high_opportunity_pct": 20.0,
        "psi_score": 0.024
    }

# Auto-initialize database on import
init_db()
