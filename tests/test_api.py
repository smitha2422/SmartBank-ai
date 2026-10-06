"""
SmartBank AI - API & Database Verification Test Suite
Comprehensive testing for Auth, Admin, Campaign Engine, and Verified Customer Banking & Deposit Safety Simulator
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from backend.app import app
from backend.database import init_db, list_all_users, get_connection

client = TestClient(app)

def setup_module():
    init_db()

def test_health_check():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert data["model_loaded"] is True

def test_auth_login_analyst():
    res = client.post("/api/auth/login", json={
        "email": "analyst@smartbank.ai",
        "password": "analyst123"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "authenticated"
    assert data["user"]["role"] == "Campaign Analyst"
    assert "Alex Mercer" in data["user"]["name"]

def test_auth_login_admin():
    res = client.post("/api/auth/login", json={
        "email": "admin@smartbank.ai",
        "password": "admin123"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "authenticated"
    assert data["user"]["role"] == "Administrator"

def test_auth_login_customer():
    res = client.post("/api/auth/login", json={
        "email": "customer@smartbank.ai",
        "password": "cust123"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "authenticated"
    assert data["user"]["role"] == "Customer"
    assert "Arthur" in data["user"]["name"]

def test_auth_register_and_login():
    reg_email = "test.operator@smartbank.ai"
    # Delete if exists from previous run
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE email = ?", (reg_email,))
    conn.commit()
    conn.close()

    res = client.post("/api/auth/register", json={
        "name": "Test Operator",
        "email": reg_email,
        "role": "Campaign Analyst",
        "department": "Direct Marketing",
        "password": "securepass123"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "registered"
    assert data["user"]["email"] == reg_email

    # Now login with the newly created employee
    login_res = client.post("/api/auth/login", json={
        "email": reg_email,
        "password": "securepass123"
    })
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert login_data["status"] == "authenticated"
    assert login_data["user"]["name"] == "Test Operator"

def test_admin_endpoints():
    # List users
    res = client.get("/api/admin/users")
    assert res.status_code == 200
    users = res.json()["users"]
    assert len(users) >= 4

    # Analytics
    res_an = client.get("/api/admin/analytics")
    assert res_an.status_code == 200
    an_data = res_an.json()
    assert "tables" in an_data
    assert "system" in an_data
    assert an_data["system"]["total_users"] >= 4

    # Provision user via admin endpoint
    res_create = client.post("/api/admin/users", json={
        "name": "Admin Created Staff",
        "email": "admin.created@smartbank.ai",
        "role": "Campaign Analyst",
        "department": "Campaign Intelligence",
        "password": "temp123"
    })
    assert res_create.status_code == 200
    created_id = res_create.json()["user"]["id"]

    # Delete the created user
    res_del = client.delete(f"/api/admin/users/{created_id}")
    assert res_del.status_code == 200
    assert res_del.json()["status"] == "deleted"

def test_customer_profile_and_financials():
    res = client.get("/api/customer/profile/customer@smartbank.ai")
    assert res.status_code == 200
    data = res.json()
    assert "salary_monthly" in data
    assert data["salary_monthly"] > 0
    assert "account_number" in data
    assert "total_emi_monthly" in data
    assert "max_deposit_limit" in data
    assert "recommended_deposit" in data
    assert "emergency_liquidity_reserve" in data
    assert data["kyc_verified"] == 1

def test_customer_verify_deposit_safe():
    res = client.post("/api/customer/verify-deposit", json={
        "customer_id": "customer@smartbank.ai",
        "deposit_amount": 1000.0,
        "tenure_months": 12
    })
    assert res.status_code == 200
    data = res.json()
    assert data["is_safe_to_deposit"] is True
    assert data["verdict"] in ["APPROVED_SAFE", "APPROVED_WITH_CAUTION"]
    assert data["projected_maturity_amount"] > 1000.0
    assert data["post_deposit_balance"] >= 0

def test_customer_verify_deposit_excessive():
    # Attempting to deposit 100,000 when balance is under 10,000
    res = client.post("/api/customer/verify-deposit", json={
        "customer_id": "CUST-001",
        "deposit_amount": 100000.0,
        "tenure_months": 12
    })
    assert res.status_code == 200
    data = res.json()
    assert data["is_safe_to_deposit"] is False
    assert data["verdict"] == "REJECTED_INSUFFICIENT_FUNDS"
    assert len(data["warning_signals"]) > 0

def test_ai_failure_risk_diagnostics():
    res = client.get("/api/ai/failure-risk/CUST-001")
    assert res.status_code == 200
    data = res.json()
    assert "failure_distress_risk_score" in data
    assert "distress_level" in data
    assert "signals" in data

def test_prediction_with_analyst_attribution():
    res = client.post("/api/predict", json={
        "customer_id": "CUST-VERIFY-01",
        "name": "Evelyn Reed",
        "analyst_name": "Sarah Vance (Admin)",
        "age": 52,
        "job": "management",
        "marital": "married",
        "education": "tertiary",
        "default": "no",
        "balance": 5400,
        "housing": "no",
        "loan": "no",
        "poutcome": "success",
        "pdays": 90,
        "previous": 2
    })
    assert res.status_code == 200
    data = res.json()
    assert "opportunity_score" in data
    assert "probability" in data
    assert data["campaign_priority"] in ["HIGH", "MEDIUM", "LOW"]
    assert len(data["predictive_signals"]) > 0

def test_optimizer_run():
    res = client.post("/api/optimizer/run", json={"capacity": 1500})
    assert res.status_code == 200
    data = res.json()
    assert "expected_conversions" in data
    assert "capacity" in data
    assert "campaign_lift_multiplier" in data

if __name__ == "__main__":
    setup_module()
    print("Running test_health_check...")
    test_health_check()
    print("Running test_auth_login_analyst...")
    test_auth_login_analyst()
    print("Running test_auth_login_admin...")
    test_auth_login_admin()
    print("Running test_auth_login_customer...")
    test_auth_login_customer()
    print("Running test_auth_register_and_login...")
    test_auth_register_and_login()
    print("Running test_admin_endpoints...")
    test_admin_endpoints()
    print("Running test_customer_profile_and_financials...")
    test_customer_profile_and_financials()
    print("Running test_customer_verify_deposit_safe...")
    test_customer_verify_deposit_safe()
    print("Running test_customer_verify_deposit_excessive...")
    test_customer_verify_deposit_excessive()
    print("Running test_ai_failure_risk_diagnostics...")
    test_ai_failure_risk_diagnostics()
    print("Running test_prediction_with_analyst_attribution...")
    test_prediction_with_analyst_attribution()
    print("Running test_optimizer_run...")
    test_optimizer_run()
    print("\n[SUCCESS] All 12 API & Database Verification Tests PASSED Successfully!")
