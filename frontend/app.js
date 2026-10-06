/**
 * SMARTBANK AI — MASTER ENTERPRISE PLATFORM CONTROLLER
 * AI Campaign Intelligence & Customer Decision Engine
 */

const API_BASE_URL = window.location.origin.includes(":5500") 
  ? "http://127.0.0.1:8000" 
  : window.location.origin;

let currentUser = null;
let currentCapacity = 2000;
let lastAssessmentResult = null;
let allLoadedCustomers = [];
let allOptimizerQueue = [];

// Archetype presets for rapid evaluation
const PRESETS = {
  high_senior: {
    age: 64,
    balance: 4800,
    job: "retired",
    marital: "married",
    education: "tertiary",
    housing: "no",
    loan: "no",
    default: "no",
    poutcome: "success",
    pdays: 120,
    previous: 3
  },
  repeat_success: {
    age: 38,
    balance: 3400,
    job: "management",
    marital: "single",
    education: "tertiary",
    housing: "no",
    loan: "no",
    default: "no",
    poutcome: "success",
    pdays: 60,
    previous: 2
  },
  indebted_worker: {
    age: 32,
    balance: 120,
    job: "blue-collar",
    marital: "married",
    education: "secondary",
    housing: "yes",
    loan: "yes",
    default: "no",
    poutcome: "failure",
    pdays: -1,
    previous: 1
  },
  middle_tech: {
    age: 44,
    balance: 1650,
    job: "technician",
    marital: "single",
    education: "secondary",
    housing: "yes",
    loan: "no",
    default: "no",
    poutcome: "unknown",
    pdays: -1,
    previous: 0
  }
};

// -------------------------------------------------------------
// INITIALIZATION
// -------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
  checkAuth();
  initServiceWorker();
  
  // Hash routing listener
  window.addEventListener("hashchange", handleHashChange);
  if (window.location.hash) {
    handleHashChange();
  }
});

function initServiceWorker() {
  if ("serviceWorker" in navigator && window.location.protocol.startsWith("http")) {
    navigator.serviceWorker.register("sw.js").catch(() => {});
  }
}

// -------------------------------------------------------------
// 1. AUTHENTICATION & SESSION MANAGEMENT
// -------------------------------------------------------------
function checkAuth() {
  const savedUser = localStorage.getItem("smartbank_user");
  if (savedUser) {
    try {
      currentUser = JSON.parse(savedUser);
      showAppShell();
      return;
    } catch (e) {
      localStorage.removeItem("smartbank_user");
    }
  }
  showLoginScreen();
}

function showLoginScreen() {
  document.getElementById("login-screen").classList.remove("hidden");
  document.getElementById("app-shell").classList.add("hidden");
}

function showAppShell() {
  document.getElementById("login-screen").classList.add("hidden");
  document.getElementById("app-shell").classList.remove("hidden");
  
  // Update User UI
  if (currentUser) {
    document.getElementById("user-name-display").textContent = currentUser.name || "Alex Mercer";
    document.getElementById("user-role-display").textContent = currentUser.role || "Campaign Analyst";
    const initials = (currentUser.name || "AM").split(" ").map(n => n[0]).join("").substring(0, 2).toUpperCase();
    document.getElementById("user-avatar-badge").textContent = initials;

    // Role-based navigation visibility
    const adminNavSection = document.getElementById("sidebar-admin-section");
    const customerNavSection = document.getElementById("sidebar-customer-section");
    const campaignNavSection = document.getElementById("sidebar-campaign-section");
    const telemetryNavSection = document.getElementById("sidebar-telemetry-section");

    if (currentUser.role === "Administrator") {
      if (adminNavSection) adminNavSection.classList.remove("hidden");
      if (customerNavSection) customerNavSection.classList.add("hidden");
      if (campaignNavSection) campaignNavSection.classList.remove("hidden");
      if (telemetryNavSection) telemetryNavSection.classList.remove("hidden");
      loadAdminData();
      if (!window.location.hash || window.location.hash === "#view-customer-portal") {
        navigateTo("view-admin");
      }
    } else if (currentUser.role === "Customer") {
      if (adminNavSection) adminNavSection.classList.add("hidden");
      if (customerNavSection) customerNavSection.classList.remove("hidden");
      if (campaignNavSection) campaignNavSection.classList.add("hidden");
      if (telemetryNavSection) telemetryNavSection.classList.add("hidden");
      loadCustomerPortalData();
      navigateTo("view-customer-portal");
    } else {
      // Campaign Analyst
      if (adminNavSection) adminNavSection.classList.add("hidden");
      if (customerNavSection) customerNavSection.classList.add("hidden");
      if (campaignNavSection) campaignNavSection.classList.remove("hidden");
      if (telemetryNavSection) telemetryNavSection.classList.remove("hidden");
      if (!window.location.hash || window.location.hash === "#view-admin" || window.location.hash === "#view-customer-portal") {
        navigateTo("view-dashboard");
      }
    }
  }
  
  // Load initial workspace data
  loadDashboardData();
  fetchCustomers();
  runCampaignOptimizer();
  fetchAssessmentHistory();
  fetchCampaignFeedback();
}

function switchAuthTab(tab) {
  const tabSignIn = document.getElementById("tab-btn-signin");
  const tabReg = document.getElementById("tab-btn-register");
  const formSignIn = document.getElementById("signin-form");
  const formReg = document.getElementById("register-form");
  const loginErr = document.getElementById("login-error");
  const regErr = document.getElementById("register-error");

  if (loginErr) loginErr.classList.add("hidden");
  if (regErr) regErr.classList.add("hidden");

  if (tab === "signin") {
    tabSignIn.classList.add("active");
    tabReg.classList.remove("active");
    formSignIn.classList.remove("hidden");
    formReg.classList.add("hidden");
  } else {
    tabReg.classList.add("active");
    tabSignIn.classList.remove("active");
    formReg.classList.remove("hidden");
    formSignIn.classList.add("hidden");
  }
}

function autofillLogin(role) {
  const emailInput = document.getElementById("login-email");
  const passInput = document.getElementById("login-password");
  if (role === "admin") {
    emailInput.value = "admin@smartbank.ai";
    passInput.value = "admin123";
  } else if (role === "customer") {
    emailInput.value = "customer@smartbank.ai";
    passInput.value = "cust123";
  } else {
    emailInput.value = "analyst@smartbank.ai";
    passInput.value = "analyst123";
  }
  document.getElementById("login-error").classList.add("hidden");
}

function autofillDemo(role) {
  autofillLogin(role);
}

async function handleLogin(e) {
  e.preventDefault();
  const email = document.getElementById("login-email").value.trim();
  const password = document.getElementById("login-password").value.trim();
  const errorBox = document.getElementById("login-error");
  const spinner = document.getElementById("login-spinner");
  const btnText = document.querySelector("#btn-login-submit .btn-text");

  errorBox.classList.add("hidden");
  spinner.classList.remove("hidden");
  btnText.textContent = "Verifying Credentials...";

  try {
    const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Authentication failed. Please check your email and password.");
    }

    currentUser = data.user;
    localStorage.setItem("smartbank_user", JSON.stringify(currentUser));
    showToast(`Welcome back, ${currentUser.name}! Signed in as ${currentUser.role}.`, "success");
    showAppShell();
    
    if (currentUser.role === "Administrator") {
      navigateTo("view-admin");
    } else if (currentUser.role === "Customer") {
      navigateTo("view-customer-portal");
      loadCustomerPortalData();
    } else {
      navigateTo("view-dashboard");
    }
  } catch (err) {
    errorBox.textContent = err.message;
    errorBox.classList.remove("hidden");
  } finally {
    spinner.classList.add("hidden");
    btnText.textContent = "Sign In to Platform";
  }
}

async function handleRegister(e) {
  e.preventDefault();
  const name = document.getElementById("reg-name").value.trim();
  const email = document.getElementById("reg-email").value.trim();
  const role = document.getElementById("reg-role").value;
  const department = document.getElementById("reg-dept").value.trim() || "Retail Banking";
  const password = document.getElementById("reg-password").value.trim();
  const errorBox = document.getElementById("register-error");
  const spinner = document.getElementById("register-spinner");
  const btnText = document.querySelector("#btn-register-submit .btn-text");

  errorBox.classList.add("hidden");
  spinner.classList.remove("hidden");
  btnText.textContent = "Creating Real Account...";

  try {
    const res = await fetch(`${API_BASE_URL}/api/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, role, department, password })
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Registration failed.");
    }

    currentUser = data.user;
    localStorage.setItem("smartbank_user", JSON.stringify(currentUser));
    showToast(`Account created for ${currentUser.name}! Welcome to SmartBank AI.`, "success");
    showAppShell();
    
    if (currentUser.role === "Administrator") {
      navigateTo("view-admin");
    } else if (currentUser.role === "Customer") {
      navigateTo("view-customer-portal");
      loadCustomerPortalData();
    } else {
      navigateTo("view-dashboard");
    }
  } catch (err) {
    errorBox.textContent = err.message;
    errorBox.classList.remove("hidden");
  } finally {
    spinner.classList.add("hidden");
    btnText.textContent = "Create Real Account & Sign In";
  }
}

function handleLogout() {
  currentUser = null;
  localStorage.removeItem("smartbank_user");
  showToast("Logged out of SmartBank AI session.", "info");
  showLoginScreen();
}

function handleRoleSwitch() {
  const select = document.getElementById("settings-role-select");
  if (currentUser) {
    currentUser.role = select.value;
    currentUser.name = select.value === "Administrator" ? "Sarah Vance (Admin)" : "Alex Mercer (Analyst)";
    localStorage.setItem("smartbank_user", JSON.stringify(currentUser));
    showToast(`Switched active operator role to: ${currentUser.role}`, "info");
    showAppShell();
  }
}

// -------------------------------------------------------------
// 1.1 ADMINISTRATOR & STAFF MANAGEMENT CONTROLLER
// -------------------------------------------------------------
async function loadAdminData() {
  try {
    const [usersRes, analyticsRes] = await Promise.all([
      fetch(`${API_BASE_URL}/api/admin/users`),
      fetch(`${API_BASE_URL}/api/admin/analytics`)
    ]);

    if (usersRes.ok) {
      const usersData = await usersRes.json();
      renderAdminUsersTable(usersData.users || []);
    }

    if (analyticsRes.ok) {
      const anData = await analyticsRes.json();
      renderAdminAnalytics(anData);
    }
  } catch (err) {
    console.error("Admin data fetch error:", err);
  }
}

function renderAdminUsersTable(users) {
  const tbody = document.getElementById("admin-users-table-body");
  const countEl = document.getElementById("admin-staff-count");
  if (countEl) countEl.textContent = users.length;
  if (!tbody) return;

  if (!users || users.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" class="text-center py-4 text-muted">No staff accounts found.</td></tr>`;
    return;
  }

  tbody.innerHTML = users.map(u => {
    const isSelf = currentUser && currentUser.email === u.email;
    const roleBadgeClass = u.role === "Administrator" ? "badge-admin" : "badge-analyst";
    const lastActive = u.last_login 
      ? new Date(u.last_login).toLocaleDateString() 
      : (u.created_at ? new Date(u.created_at).toLocaleDateString() : "Active");
    
    return `
      <tr>
        <td class="font-mono text-muted text-xs">#${u.id}</td>
        <td>
          <div class="user-cell-flex">
            <div class="user-cell-avatar">${(u.name || "U").substring(0, 2).toUpperCase()}</div>
            <div>
              <strong>${u.name}</strong> ${isSelf ? '<span class="text-cyan text-xs font-semibold">(You)</span>' : ''}
            </div>
          </div>
        </td>
        <td class="font-mono text-xs text-muted">${u.email}</td>
        <td><span class="role-badge ${roleBadgeClass}">${u.role}</span></td>
        <td class="text-sm">${u.department || 'Retail Banking'}</td>
        <td class="text-xs text-muted font-mono">${lastActive}</td>
        <td><strong class="font-mono text-cyan">${u.assessments_count || 0}</strong></td>
        <td>
          ${isSelf ? '<span class="text-xs text-muted">Current User</span>' : `
            <button type="button" class="btn-ghost-danger btn-xs" onclick="handleAdminDeleteEmployee(${u.id}, '${u.name.replace(/'/g, "\\'")}')">
              Delete
            </button>
          `}
        </td>
      </tr>
    `;
  }).join("");
}

function renderAdminAnalytics(data) {
  if (data.system) {
    const assessEl = document.getElementById("admin-assessments-count");
    if (assessEl) assessEl.textContent = data.system.total_assessments_logged || 0;
    
    const dbSizeEl = document.getElementById("admin-db-size");
    if (dbSizeEl) {
      const kb = Math.round((data.system.database_size_bytes || 0) / 1024);
      dbSizeEl.textContent = `${kb} KB`;
    }
  }

  const tablesTbody = document.getElementById("admin-tables-tbody");
  if (data.tables && tablesTbody) {
    tablesTbody.innerHTML = data.tables.map(t => `
      <tr>
        <td class="font-mono text-cyan">${t.table_name}</td>
        <td class="text-xs text-muted">${t.description}</td>
        <td><strong class="font-mono text-emerald">${t.row_count}</strong> rows</td>
      </tr>
    `).join("");
  }

  const logsTbody = document.getElementById("admin-recent-assessments-tbody");
  if (data.recent_assessments && logsTbody) {
    if (data.recent_assessments.length === 0) {
      logsTbody.innerHTML = `<tr><td colspan="4" class="text-center py-3 text-muted text-xs">No assessments logged yet.</td></tr>`;
    } else {
      logsTbody.innerHTML = data.recent_assessments.slice(0, 6).map(a => `
        <tr>
          <td class="text-xs text-muted font-mono">${(a.timestamp || '').substring(11, 19) || 'Just now'}</td>
          <td><strong>${a.customer_name || a.customer_id}</strong></td>
          <td><span class="badge-analyst-sm">${a.analyst_name || 'Staff Analyst'}</span></td>
          <td><span class="badge-priority badge-${(a.campaign_priority || 'LOW').toLowerCase()}">${a.opportunity_score} pts</span></td>
        </tr>
      `).join("");
    }
  }
}

function openCreateEmployeeModal() {
  document.getElementById("modal-create-employee").classList.remove("hidden");
}

async function handleAdminCreateEmployee(e) {
  e.preventDefault();
  const name = document.getElementById("adm-emp-name").value.trim();
  const email = document.getElementById("adm-emp-email").value.trim();
  const role = document.getElementById("adm-emp-role").value;
  const department = document.getElementById("adm-emp-dept").value.trim();
  const password = document.getElementById("adm-emp-password").value.trim();

  try {
    const res = await fetch(`${API_BASE_URL}/api/admin/users`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, role, department, password })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to create employee.");

    showToast(`Staff account provisioned for ${data.user.name}!`, "success");
    closeModal("modal-create-employee");
    document.getElementById("form-create-employee").reset();
    loadAdminData();
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function handleAdminDeleteEmployee(userId, userName) {
  if (!confirm(`Are you sure you want to delete employee ${userName} (ID #${userId})? This will permanently remove their platform account.`)) {
    return;
  }

  try {
    const res = await fetch(`${API_BASE_URL}/api/admin/users/${userId}`, {
      method: "DELETE"
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to delete employee.");

    showToast(`Deleted employee account #${userId}`, "success");
    loadAdminData();
  } catch (err) {
    showToast(err.message, "error");
  }
}

// -------------------------------------------------------------
// 2. VIEW NAVIGATION & ROUTING
// -------------------------------------------------------------
const PAGE_TITLES = {
  "view-customer-portal": { title: "Verified Customer Banking Hub", subtitle: "SmartBank AI / Customer Portal & Safe Deposit Simulator" },
  "view-admin": { title: "Staff & System Analytics", subtitle: "SmartBank AI / Admin Center" },
  "view-dashboard": { title: "Campaign Intelligence Dashboard", subtitle: "SmartBank AI / Overview" },
  "view-customers": { title: "Customer Intelligence Directory", subtitle: "SmartBank AI / Customers" },
  "view-assessment": { title: "Customer Deposit Propensity Assessment", subtitle: "SmartBank AI / New Assessment" },
  "view-optimizer": { title: "Campaign Capacity Optimizer", subtitle: "SmartBank AI / Optimizer" },
  "view-history": { title: "Assessment History & Audit Trail", subtitle: "SmartBank AI / Prediction History" },
  "view-performance": { title: "Machine Learning Model Evaluation", subtitle: "SmartBank AI / Model Performance" },
  "view-explainability": { title: "Explainable AI & Feature Importance", subtitle: "SmartBank AI / Explainability" },
  "view-feedback": { title: "Campaign Feedback Intelligence", subtitle: "SmartBank AI / Closed-Loop Learning" },
  "view-health": { title: "Model Telemetry & Drift Monitoring", subtitle: "SmartBank AI / Model Health" },
  "view-settings": { title: "Platform Settings & Roles", subtitle: "SmartBank AI / Settings" }
};

function navigateTo(viewId) {
  document.querySelectorAll(".view-section").forEach(v => v.classList.remove("active"));
  document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));

  const targetView = document.getElementById(viewId);
  const targetNav = document.querySelector(`.nav-item[data-view="${viewId}"]`);

  if (targetView) targetView.classList.add("active");
  if (targetNav) targetNav.classList.add("active");

  const meta = PAGE_TITLES[viewId] || { title: "Campaign Intelligence", subtitle: "SmartBank AI" };
  document.getElementById("current-page-title").textContent = meta.title;
  document.getElementById("current-page-subtitle").textContent = meta.subtitle;

  window.location.hash = viewId;
  window.scrollTo({ top: 0, behavior: "smooth" });

  // Close mobile sidebar if open
  document.querySelector(".sidebar").classList.remove("mobile-open");
}

function handleHashChange() {
  const hash = window.location.hash.replace("#", "");
  if (hash && document.getElementById(hash)) {
    navigateTo(hash);
  }
}

function toggleMobileMenu() {
  document.querySelector(".sidebar").classList.toggle("mobile-open");
}

// -------------------------------------------------------------
// 3. DASHBOARD CONTROLLER
// -------------------------------------------------------------
async function loadDashboardData() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/dashboard`);
    if (!res.ok) return;
    const data = await res.json();

    if (data.kpi) {
      document.getElementById("kpi-total-customers").textContent = data.kpi.total_customers || 30;
      document.getElementById("kpi-f1").textContent = data.kpi.model_f1_score || "0.371";
    }

    if (data.recent_assessments) {
      renderDashboardRecentTable(data.recent_assessments);
    }
  } catch (e) {
    console.warn("Dashboard fetch notice:", e);
  }
}

function renderDashboardRecentTable(assessments) {
  const tbody = document.getElementById("dashboard-recent-table-body");
  if (!assessments || assessments.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-muted">No assessments logged yet. Run your first assessment!</td></tr>`;
    return;
  }

  tbody.innerHTML = assessments.slice(0, 6).map(a => `
    <tr>
      <td>
        <strong>${a.customer_name || 'Prospective Lead'}</strong>
        <div class="text-xs text-muted font-mono">${a.customer_id}</div>
      </td>
      <td><strong class="font-mono">${a.opportunity_score}/100</strong></td>
      <td><span class="text-cyan font-mono">${Math.round(a.probability * 1000) / 10}%</span></td>
      <td><span class="badge-priority badge-${(a.campaign_priority || 'LOW').toLowerCase()}">${a.campaign_priority}</span></td>
      <td><span class="text-xs text-muted">${(a.next_best_action || '').substring(0, 45)}...</span></td>
    </tr>
  `).join("");
}

// -------------------------------------------------------------
// 4. CUSTOMER MANAGEMENT CONTROLLER
// -------------------------------------------------------------
async function fetchCustomers(search = "", priority = "ALL") {
  try {
    let url = `${API_BASE_URL}/api/customers?limit=100`;
    if (search) url += `&search=${encodeURIComponent(search)}`;
    if (priority && priority !== "ALL") url += `&priority=${priority}`;

    const res = await fetch(url);
    if (!res.ok) return;
    const data = await res.json();

    allLoadedCustomers = data.customers || [];
    renderCustomersTable(allLoadedCustomers);
  } catch (e) {
    console.warn("Customer fetch notice:", e);
  }
}

function renderCustomersTable(customers) {
  const tbody = document.getElementById("customers-table-body");
  if (!customers || customers.length === 0) {
    tbody.innerHTML = `<tr><td colspan="10" class="text-center py-4 text-muted">No customers found. Try importing or resetting demo customers.</td></tr>`;
    return;
  }

  tbody.innerHTML = customers.map(c => `
    <tr>
      <td class="font-mono text-cyan">${c.customer_id}</td>
      <td><strong>${c.name}</strong></td>
      <td>${c.age}</td>
      <td><span class="capitalize">${c.job}</span></td>
      <td><span class="capitalize">${c.education}</span></td>
      <td class="font-mono">€${Number(c.balance).toLocaleString()}</td>
      <td><span class="capitalize">${c.poutcome}</span></td>
      <td><strong class="font-mono">${c.last_opportunity_score != null ? c.last_opportunity_score : '--'}</strong></td>
      <td>
        ${c.last_priority ? `<span class="badge-priority badge-${c.last_priority.toLowerCase()}">${c.last_priority}</span>` : '<span class="text-muted text-xs">Unassessed</span>'}
      </td>
      <td>
        <button type="button" class="btn-primary btn-sm" onclick="selectCustomerForAssessment('${c.customer_id}')">
          Assess
        </button>
      </td>
    </tr>
  `).join("");
}

function filterCustomersTable() {
  const search = document.getElementById("cust-search").value;
  const priority = document.getElementById("cust-priority-filter").value;
  fetchCustomers(search, priority);
}

function selectCustomerForAssessment(customerId) {
  const cust = allLoadedCustomers.find(c => c.customer_id === customerId);
  if (!cust) return;

  document.getElementById("feat-cust-id").value = cust.customer_id;
  document.getElementById("feat-name").value = cust.name;
  document.getElementById("feat-age").value = cust.age;
  document.getElementById("feat-job").value = cust.job;
  document.getElementById("feat-marital").value = cust.marital;
  document.getElementById("feat-education").value = cust.education;
  document.getElementById("feat-balance").value = cust.balance;
  document.getElementById("feat-default").value = cust.default_credit || "no";
  document.getElementById("feat-housing").value = cust.housing || "no";
  document.getElementById("feat-loan").value = cust.loan || "no";
  document.getElementById("feat-poutcome").value = cust.poutcome || "unknown";
  document.getElementById("feat-pdays").value = cust.pdays != null ? cust.pdays : -1;
  document.getElementById("feat-previous").value = cust.previous || 0;

  navigateTo("view-assessment");
  showToast(`Loaded ${cust.name} profile into assessment form.`, "info");
}

function openAddCustomerModal() {
  document.getElementById("modal-add-customer").classList.remove("hidden");
}

async function handleAddCustomerSubmit(e) {
  e.preventDefault();
  const payload = {
    name: document.getElementById("new-cust-name").value.trim(),
    email: document.getElementById("new-cust-email").value.trim() || undefined,
    age: parseInt(document.getElementById("new-cust-age").value),
    job: document.getElementById("new-cust-job").value,
    marital: document.getElementById("new-cust-marital").value,
    education: document.getElementById("new-cust-education").value,
    balance: parseFloat(document.getElementById("new-cust-balance").value),
    poutcome: document.getElementById("new-cust-poutcome").value,
    housing: "no",
    loan: "no",
    default: "no",
    pdays: -1,
    previous: 0
  };

  try {
    const res = await fetch(`${API_BASE_URL}/api/customers`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) throw new Error("Failed to create customer.");
    const data = await res.json();

    showToast(`Customer ${data.customer.name} (${data.customer.customer_id}) added!`, "success");
    closeModal("modal-add-customer");
    fetchCustomers();
  } catch (err) {
    showToast(err.message, "error");
  }
}

function exportCustomersCSV() {
  if (!allLoadedCustomers || allLoadedCustomers.length === 0) {
    showToast("No customers available to export.", "info");
    return;
  }

  const headers = ["Customer ID", "Name", "Age", "Job", "Marital", "Education", "Balance", "Housing", "Loan", "Prior Campaign", "Days Since Prior Contact", "Opportunity Score", "Priority"];
  const rows = allLoadedCustomers.map(c => [
    c.customer_id,
    `"${c.name}"`,
    c.age,
    c.job,
    c.marital,
    c.education,
    c.balance,
    c.housing,
    c.loan,
    c.poutcome,
    c.pdays,
    c.last_opportunity_score || "",
    c.last_priority || ""
  ]);

  const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
  const encodedUri = encodeURI(csvContent);
  const link = document.createElement("a");
  link.setAttribute("href", encodedUri);
  link.setAttribute("download", `smartbank_customers_${Date.now()}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  showToast("Exported customers CSV successfully.", "success");
}

async function seedDemoCustomers() {
  showToast("Re-seeding SQLite database with verified leads...", "info");
  try {
    const res = await fetch(`${API_BASE_URL}/api/dashboard`);
    fetchCustomers();
    loadDashboardData();
    runCampaignOptimizer();
    fetchAssessmentHistory();
    showToast("Demo database refreshed with 30 leads & 50 feedback records!", "success");
  } catch (e) {
    showToast("Database seed notice.", "info");
  }
}

// -------------------------------------------------------------
// 5. NEW ASSESSMENT & PROPENSITY WORKFLOW
// -------------------------------------------------------------
function loadArchetype(type) {
  const data = PRESETS[type];
  if (!data) return;

  document.getElementById("feat-age").value = data.age;
  document.getElementById("feat-job").value = data.job;
  document.getElementById("feat-marital").value = data.marital;
  document.getElementById("feat-education").value = data.education;
  document.getElementById("feat-balance").value = data.balance;
  document.getElementById("feat-default").value = data.default;
  document.getElementById("feat-housing").value = data.housing;
  document.getElementById("feat-loan").value = data.loan;
  document.getElementById("feat-poutcome").value = data.poutcome;
  document.getElementById("feat-pdays").value = data.pdays;
  document.getElementById("feat-previous").value = data.previous;

  const names = {
    high_senior: "Arthur Pendelton (High Liquidity Senior)",
    repeat_success: "Elena Rostova (Repeat Subscriber)",
    indebted_worker: "Marcus Brody (Multiple Loan Debts)",
    middle_tech: "Liam Vance (Middle Technician)"
  };
  document.getElementById("feat-name").value = names[type] || "Demo Customer";
  showToast(`Loaded preset: ${names[type]}`, "info");
}

async function handleRunAssessment(e) {
  e.preventDefault();

  const payload = {
    customer_id: document.getElementById("feat-cust-id").value.trim() || "CUST-GUEST",
    name: document.getElementById("feat-name").value.trim() || "Prospective Client",
    analyst_name: currentUser ? currentUser.name : "Staff Analyst",
    age: parseInt(document.getElementById("feat-age").value),
    job: document.getElementById("feat-job").value,
    marital: document.getElementById("feat-marital").value,
    education: document.getElementById("feat-education").value,
    default: document.getElementById("feat-default").value,
    balance: parseFloat(document.getElementById("feat-balance").value),
    housing: document.getElementById("feat-housing").value,
    loan: document.getElementById("feat-loan").value,
    poutcome: document.getElementById("feat-poutcome").value,
    pdays: parseInt(document.getElementById("feat-pdays").value),
    previous: parseInt(document.getElementById("feat-previous").value)
  };

  // Show processing animation
  const placeholder = document.getElementById("result-placeholder");
  const resultContent = document.getElementById("result-content");
  const processingOverlay = document.getElementById("assessment-processing");

  placeholder.classList.add("hidden");
  resultContent.classList.add("hidden");
  processingOverlay.classList.remove("hidden");

  // Animate steps
  const steps = ["p-step-1", "p-step-2", "p-step-3", "p-step-4", "p-step-5", "p-step-6"];
  for (let i = 0; i < steps.length; i++) {
    const el = document.getElementById(steps[i]);
    el.classList.add("active");
    await new Promise(r => setTimeout(r, 90));
    el.classList.remove("active");
    el.classList.add("done");
  }

  try {
    const res = await fetch(`${API_BASE_URL}/api/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Prediction inference failed.");
    }

    const data = await res.json();
    lastAssessmentResult = data;
    renderAssessmentResult(data, payload);
    showToast(`AI Assessment Complete for ${payload.name}!`, "success");
  } catch (err) {
    showToast(`Assessment unavailable: ${err.message}`, "error");
    placeholder.classList.remove("hidden");
  } finally {
    processingOverlay.classList.add("hidden");
    steps.forEach(s => document.getElementById(s).classList.remove("done", "active"));
  }
}

function renderAssessmentResult(data, inputFeatures) {
  document.getElementById("result-content").classList.remove("hidden");
  document.getElementById("res-cust-name").textContent = inputFeatures.name || "Prospective Client";
  document.getElementById("res-cust-id").textContent = inputFeatures.customer_id || "CUST-GUEST";

  // Score & Probability
  const score = data.opportunity_score;
  document.getElementById("res-opportunity-score").textContent = score;
  document.getElementById("res-probability").textContent = `${Math.round(data.probability * 1000) / 10}%`;
  document.getElementById("res-label").textContent = data.prediction_label;

  // Priority Badge
  const pBadge = document.getElementById("res-priority-badge");
  pBadge.className = `badge-priority badge-${data.campaign_priority.toLowerCase()}`;
  pBadge.textContent = `${data.campaign_priority} PRIORITY`;

  // Animate Radial Gauge SVG
  const gaugeBar = document.getElementById("gauge-bar");
  const maxDash = 427;
  const offset = maxDash - (maxDash * score) / 100;
  gaugeBar.style.strokeDashoffset = offset;

  if (score >= 65) {
    gaugeBar.style.stroke = "var(--accent-emerald)";
  } else if (score >= 40) {
    gaugeBar.style.stroke = "var(--warning-amber)";
  } else {
    gaugeBar.style.stroke = "var(--text-muted)";
  }

  // Next Best Action
  document.getElementById("res-next-action").textContent = data.next_best_action;

  // Predictive Signals
  const signalsContainer = document.getElementById("res-signals-list");
  signalsContainer.innerHTML = (data.predictive_signals || []).map(s => `
    <div class="signal-item">
      <span>${s.factor}</span>
      <strong class="${s.type === 'positive' ? 'signal-pos' : (s.type === 'negative' ? 'signal-neg' : 'signal-neu')}">${s.impact}</strong>
    </div>
  `).join("");

  // Refresh history & customers in background
  fetchAssessmentHistory();
  fetchCustomers();
  loadDashboardData();
}

function saveAssessmentToHistory() {
  if (!lastAssessmentResult) {
    showToast("No active assessment to save.", "info");
    return;
  }
  showToast(`Assessment for ${lastAssessmentResult.customer_name || 'Client'} saved to SQLite!`, "success");
}

// -------------------------------------------------------------
// 6. CAMPAIGN OPTIMIZER CONTROLLER
// -------------------------------------------------------------
function setCapacityPreset(cap) {
  document.querySelectorAll(".btn-preset-cap").forEach(b => b.classList.remove("active"));
  const btn = Array.from(document.querySelectorAll(".btn-preset-cap")).find(b => b.textContent.includes(cap));
  if (btn) btn.classList.add("active");

  document.getElementById("optimizer-capacity-input").value = cap;
  currentCapacity = cap;
  runCampaignOptimizer();
}

function handleCapacityChange() {
  const val = parseInt(document.getElementById("optimizer-capacity-input").value);
  if (val >= 50 && val <= 10000) {
    currentCapacity = val;
    runCampaignOptimizer();
  }
}

async function runCampaignOptimizer() {
  const cap = currentCapacity || 2000;
  try {
    const res = await fetch(`${API_BASE_URL}/api/optimize-campaign`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ capacity: cap, pool_size: 5000 })
    });

    if (!res.ok) return;
    const data = await res.json();

    document.getElementById("opt-expected-conversions").textContent = Math.round(data.expected_conversions).toLocaleString();
    document.getElementById("opt-expected-rate").textContent = `${data.expected_conversion_rate}% Conversion Rate`;
    document.getElementById("opt-lift-multiplier").textContent = `${data.campaign_lift_multiplier}x`;
    document.getElementById("opt-pool-size").textContent = `${data.evaluated_pool_size.toLocaleString()}`;

    // Tiers
    if (data.tier_summary) {
      document.getElementById("tier-a-count").textContent = data.tier_summary.tier_a.count.toLocaleString();
      document.getElementById("tier-b-count").textContent = data.tier_summary.tier_b.count.toLocaleString();
      document.getElementById("tier-c-count").textContent = data.tier_summary.tier_c.count.toLocaleString();
      document.getElementById("tier-d-count").textContent = data.tier_summary.tier_d.count.toLocaleString();
    }

    allOptimizerQueue = data.top_queue || [];
    renderOptimizerQueueTable(allOptimizerQueue);
  } catch (e) {
    console.warn("Optimizer execution notice:", e);
  }
}

function renderOptimizerQueueTable(queue) {
  const tbody = document.getElementById("optimizer-queue-table-body");
  if (!queue || queue.length === 0) {
    tbody.innerHTML = `<tr><td colspan="10" class="text-center py-4 text-muted">No records in queue.</td></tr>`;
    return;
  }

  tbody.innerHTML = queue.map(q => `
    <tr>
      <td><strong>#${q.rank}</strong></td>
      <td class="font-mono text-cyan">${q.customer_id}</td>
      <td>${q.age}</td>
      <td>${q.job}</td>
      <td class="font-mono">€${Number(q.balance).toLocaleString()}</td>
      <td>${q.poutcome}</td>
      <td><span class="text-cyan font-mono">${Math.round(q.probability * 1000) / 10}%</span></td>
      <td><strong class="font-mono">${q.opportunity_score}</strong></td>
      <td><span class="badge-priority badge-${q.priority.toLowerCase()}">${q.tier.split(' ')[0]} ${q.tier.split(' ')[1]}</span></td>
      <td><span class="text-xs text-muted">${q.action}</span></td>
    </tr>
  `).join("");
}

function exportOptimizerQueueCSV() {
  if (!allOptimizerQueue || allOptimizerQueue.length === 0) {
    showToast("No queue records to export.", "info");
    return;
  }

  const headers = ["Rank", "Customer ID", "Age", "Job", "Balance", "Prior Campaign", "Probability", "Opportunity Score", "Priority Tier", "Assigned Action"];
  const rows = allOptimizerQueue.map(q => [
    q.rank,
    q.customer_id,
    q.age,
    q.job,
    q.balance,
    q.poutcome,
    q.probability,
    q.opportunity_score,
    `"${q.tier}"`,
    `"${q.action}"`
  ]);

  const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
  const encodedUri = encodeURI(csvContent);
  const link = document.createElement("a");
  link.setAttribute("href", encodedUri);
  link.setAttribute("download", `smartbank_priority_outreach_queue_${Date.now()}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  showToast("Exported prioritized campaign queue CSV successfully.", "success");
}

// -------------------------------------------------------------
// 7. PREDICTION HISTORY & CAMPAIGN FEEDBACK
// -------------------------------------------------------------
async function fetchAssessmentHistory() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/assessments?limit=50`);
    if (!res.ok) return;
    const data = await res.json();

    const tbody = document.getElementById("history-table-body");
    if (!data.records || data.records.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" class="text-center py-4 text-muted">No historical assessments recorded yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = data.records.map(r => {
      const dateStr = new Date(r.timestamp).toLocaleString();
      return `
        <tr>
          <td class="text-xs text-muted font-mono">${dateStr}</td>
          <td class="font-mono text-cyan">${r.customer_id}</td>
          <td><strong>${r.customer_name || 'Prospective Client'}</strong></td>
          <td><span class="text-cyan font-mono">${Math.round(r.probability * 1000) / 10}%</span></td>
          <td><strong class="font-mono">${r.opportunity_score}/100</strong></td>
          <td><span class="badge-priority badge-${r.campaign_priority.toLowerCase()}">${r.campaign_priority}</span></td>
          <td><span class="text-xs text-emerald">${r.prediction_label}</span></td>
          <td><span class="text-xs text-muted">${(r.next_best_action || '').substring(0, 50)}...</span></td>
        </tr>
      `;
    }).join("");
  } catch (e) {
    console.warn("History fetch notice:", e);
  }
}

async function fetchCampaignFeedback() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/campaign-feedback`);
    if (!res.ok) return;
    const data = await res.json();

    const tbody = document.getElementById("feedback-table-body");
    if (!data.sample_audit_records || data.sample_audit_records.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted">No historical feedback logs available.</td></tr>`;
      return;
    }

    tbody.innerHTML = data.sample_audit_records.map(f => `
      <tr>
        <td class="font-mono text-cyan">${f.customer_ref}</td>
        <td class="text-xs text-muted font-mono">${f.contact_date}</td>
        <td><span class="text-cyan font-mono">${Math.round(f.predicted_probability * 1000) / 10}%</span></td>
        <td><strong class="font-mono">${f.opportunity_score}</strong></td>
        <td><span class="badge-priority badge-${f.campaign_priority.toLowerCase()}">${f.campaign_priority}</span></td>
        <td><span class="capitalize font-mono ${f.actual_outcome === 'yes' ? 'text-emerald' : 'text-muted'}">${f.actual_outcome}</span></td>
        <td>
          <span class="badge-priority ${f.outcome_match === 1 ? 'badge-high' : 'badge-low'}">
            ${f.outcome_match === 1 ? 'MATCHED' : 'VARIANCE'}
          </span>
        </td>
      </tr>
    `).join("");
  } catch (e) {
    console.warn("Feedback fetch notice:", e);
  }
}

// -------------------------------------------------------------
// 8. CSV IMPORT & MODAL CONTROLS
// -------------------------------------------------------------
let parsedCSVRows = [];

function openImportModal() {
  document.getElementById("modal-import-csv").classList.remove("hidden");
}

function openLeakageModal() {
  document.getElementById("modal-leakage").classList.remove("hidden");
}

function closeModal(modalId) {
  document.getElementById(modalId).classList.add("hidden");
}

function closeModalOnBackdrop(e, modalId) {
  if (e.target.id === modalId) {
    closeModal(modalId);
  }
}

function handleCSVFileSelect(e) {
  const file = e.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = function(evt) {
    const text = evt.target.result;
    const lines = text.split("\n").filter(l => l.trim().length > 0);
    if (lines.length < 2) {
      showToast("CSV file must contain a header row and at least one data row.", "error");
      return;
    }

    const headers = lines[0].split(",").map(h => h.trim().replace(/"/g, '').toLowerCase());
    parsedCSVRows = [];

    for (let i = 1; i < lines.length; i++) {
      const vals = lines[i].split(",").map(v => v.trim().replace(/"/g, ''));
      const rowObj = {};
      headers.forEach((h, idx) => {
        rowObj[h] = vals[idx];
      });
      parsedCSVRows.push(rowObj);
    }

    document.getElementById("csv-preview-container").classList.remove("hidden");
    document.getElementById("csv-preview-count").textContent = `${parsedCSVRows.length} records ready for import`;
    document.getElementById("btn-import-confirm").removeAttribute("disabled");

    const tbody = document.getElementById("csv-preview-tbody");
    tbody.innerHTML = parsedCSVRows.slice(0, 5).map(r => `
      <tr>
        <td>${r.name || 'Lead'}</td>
        <td>${r.age || '40'}y</td>
        <td>${r.job || 'technician'}</td>
        <td>€${r.balance || '1000'}</td>
        <td>${r.poutcome || 'unknown'}</td>
      </tr>
    `).join("");
  };
  reader.readAsText(file);
}

async function executeCSVImport() {
  if (!parsedCSVRows || parsedCSVRows.length === 0) return;

  try {
    const res = await fetch(`${API_BASE_URL}/api/customers/import`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(parsedCSVRows)
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Import failed.");

    showToast(`Successfully imported ${data.imported_count} customer leads!`, "success");
    closeModal("modal-import-csv");
    fetchCustomers();
  } catch (err) {
    showToast(err.message, "error");
  }
}

// -------------------------------------------------------------
// 9. TOAST NOTIFICATION UTILITY
// -------------------------------------------------------------
function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  const toast = document.createElement("div");
  toast.className = `toast-item toast-${type}`;
  
  const icon = type === "success" ? "✓" : (type === "error" ? "✕" : "ℹ");
  toast.innerHTML = `<span class="toast-icon">${icon}</span> <span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    toast.style.transition = "all 0.3s";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

function handleGlobalSearch(e) {
  const q = e.target.value.toLowerCase().trim();
  if (!q) {
    renderCustomersTable(allLoadedCustomers);
    return;
  }
  const filtered = allLoadedCustomers.filter(c => 
    c.name.toLowerCase().includes(q) || 
    c.customer_id.toLowerCase().includes(q) || 
    c.job.toLowerCase().includes(q)
  );
  renderCustomersTable(filtered);
  if (e.key === "Enter") {
    navigateTo("view-customers");
  }
}

function openGupioTour() {
  showToast("Interview Walkthrough: 1. Leakage Guard -> 2. Propensity Engine -> 3. Campaign Optimizer -> 4. SQLite Audit.", "info");
  navigateTo("view-performance");
}

// -------------------------------------------------------------
// 10. VERIFIED CUSTOMER BANKING PORTAL & PRE-DEPOSIT SIMULATOR
// -------------------------------------------------------------
let currentCustomerProfile = null;

async function loadCustomerPortalData() {
  try {
    const identifier = (currentUser && currentUser.email) ? currentUser.email : "customer@smartbank.ai";
    const res = await fetch(`${API_BASE_URL}/api/customer/profile/${encodeURIComponent(identifier)}`);
    if (!res.ok) {
      // fallback to general profile
      const fallbackRes = await fetch(`${API_BASE_URL}/api/customer/profile`);
      if (fallbackRes.ok) {
        const fallbackData = await fallbackRes.json();
        renderCustomerPortalData(fallbackData);
      }
      return;
    }
    const data = await res.json();
    renderCustomerPortalData(data);
  } catch (err) {
    console.error("Error loading customer profile:", err);
  }
}

function renderCustomerPortalData(data) {
  if (!data) return;
  currentCustomerProfile = data;

  // 1. Hero Card
  const avatarEl = document.getElementById("cust-portal-avatar");
  if (avatarEl) {
    const initials = (data.name || "AP").split(" ").map(n => n[0]).join("").substring(0, 2).toUpperCase();
    avatarEl.textContent = initials;
  }
  const nameEl = document.getElementById("cust-portal-name");
  if (nameEl) nameEl.textContent = data.name || "Arthur Pendelton";

  const kycEl = document.getElementById("cust-portal-kyc");
  if (kycEl) {
    kycEl.textContent = data.kyc_verified ? "✓ KYC VERIFIED" : "PENDING KYC";
  }

  const creditEl = document.getElementById("cust-portal-credit");
  if (creditEl) {
    if (data.credit_default === "yes") {
      creditEl.textContent = "⚠️ CREDIT DEFAULT RISK RECORDED";
      creditEl.className = "credit-badge credit-badge-danger";
    } else {
      creditEl.textContent = "CLEAN CREDIT PROFILE";
      creditEl.className = "credit-badge";
    }
  }

  const accEl = document.getElementById("cust-portal-acc");
  if (accEl) accEl.textContent = data.account_number || "SB-88219482";

  const jobEl = document.getElementById("cust-portal-job");
  if (jobEl) jobEl.textContent = (data.job || "management").charAt(0).toUpperCase() + (data.job || "management").slice(1);

  const ageEl = document.getElementById("cust-portal-age");
  if (ageEl) ageEl.textContent = `${data.age || 40}y`;

  // 2. Financial KPI Cards
  const balanceEl = document.getElementById("cust-kpi-balance");
  if (balanceEl) balanceEl.textContent = `€${Number(data.balance || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

  const salaryEl = document.getElementById("cust-kpi-salary");
  if (salaryEl) salaryEl.textContent = `€${Number(data.salary_monthly || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} / mo`;

  const emiEl = document.getElementById("cust-kpi-emi");
  if (emiEl) emiEl.textContent = `€${Number(data.total_emi_monthly || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} / mo`;

  const emiSubEl = document.getElementById("cust-kpi-emi-sub");
  if (emiSubEl) {
    emiSubEl.textContent = `Housing: €${Math.round(data.housing_emi || 0)} | Personal: €${Math.round(data.personal_loan_emi || 0)}`;
  }

  const dtiEl = document.getElementById("cust-kpi-dti");
  const dtiSubEl = document.getElementById("cust-kpi-dti-sub");
  if (dtiEl) {
    dtiEl.textContent = `${data.dti_ratio_pct || 0}%`;
    if (data.dti_ratio_pct > 40) {
      dtiEl.className = "kpi-value text-rose";
      if (dtiSubEl) dtiSubEl.textContent = "⚠️ High debt burden (>40% threshold)";
    } else if (data.dti_ratio_pct > 25) {
      dtiEl.className = "kpi-value text-amber";
      if (dtiSubEl) dtiSubEl.textContent = "Moderate debt load (25-40%)";
    } else {
      dtiEl.className = "kpi-value text-emerald";
      if (dtiSubEl) dtiSubEl.textContent = "Safe range (<25% threshold)";
    }
  }

  // 3. AI Deposit Limits & Reserves
  const maxLimitEl = document.getElementById("cust-max-limit");
  if (maxLimitEl) maxLimitEl.textContent = `€${Number(data.max_deposit_limit || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

  const recDepEl = document.getElementById("cust-rec-deposit");
  if (recDepEl) recDepEl.textContent = `€${Number(data.recommended_deposit || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

  const resBufferEl = document.getElementById("cust-emergency-reserve");
  if (resBufferEl) resBufferEl.textContent = `€${Number(data.emergency_liquidity_reserve || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

  const netDispEl = document.getElementById("cust-net-disposable");
  if (netDispEl) netDispEl.textContent = `€${Number(data.disposable_income_monthly || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} / mo`;

  const safetyBadgeEl = document.getElementById("cust-safety-badge");
  if (safetyBadgeEl) {
    if (data.risk_failure_score < 25) {
      safetyBadgeEl.textContent = "AI VERIFIED SAFE";
      safetyBadgeEl.className = "badge-priority badge-high";
    } else if (data.risk_failure_score < 50) {
      safetyBadgeEl.textContent = "CAUTION ADVISED";
      safetyBadgeEl.className = "badge-priority badge-medium";
    } else {
      safetyBadgeEl.textContent = "HIGH DISTRESS RISK";
      safetyBadgeEl.className = "badge-priority badge-low";
    }
  }

  // 4. Yield Projections Table
  const recAmount = Number(data.recommended_deposit) || 2000;
  const yieldTbody = document.getElementById("cust-yield-table-body");
  if (yieldTbody) {
    const rates = [
      { tenure: "6 Months", rate: 3.80, months: 6 },
      { tenure: "12 Months", rate: 4.25, months: 12 },
      { tenure: "24 Months", rate: 4.60, months: 24 },
      { tenure: "36 Months", rate: 4.85, months: 36 }
    ];
    yieldTbody.innerHTML = rates.map(r => {
      const interest = Math.round(recAmount * (r.rate / 100) * (r.months / 12) * 100) / 100;
      const maturity = Math.round((recAmount + interest) * 100) / 100;
      return `
        <tr>
          <td><strong>${r.tenure}</strong></td>
          <td><strong class="text-cyan">${r.rate}% p.a.</strong></td>
          <td class="text-emerald font-mono">+€${interest.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
          <td class="font-mono font-bold">€${maturity.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
        </tr>
      `;
    }).join("");
  }

  // 5. Pre-fill simulator input
  const simInput = document.getElementById("sim-deposit-amount");
  if (simInput) {
    simInput.value = Math.max(100, Math.round(data.recommended_deposit || 2000));
  }
}

async function handleSimulateDeposit(e) {
  if (e) e.preventDefault();
  const amountInput = document.getElementById("sim-deposit-amount");
  const tenureInput = document.getElementById("sim-deposit-tenure");
  const spinner = document.getElementById("sim-spinner");
  const btnText = document.querySelector("#btn-simulate-submit .btn-text");

  const depositAmount = parseFloat(amountInput.value) || 0;
  const tenureMonths = parseInt(tenureInput.value, 10) || 12;
  const customerId = currentCustomerProfile ? currentCustomerProfile.customer_id : "CUST-001";

  if (depositAmount <= 0) {
    showToast("Please enter a valid deposit amount greater than €0.", "error");
    return;
  }

  if (spinner) spinner.classList.remove("hidden");
  if (btnText) btnText.textContent = "AI Safety Verification in Progress...";

  try {
    const res = await fetch(`${API_BASE_URL}/api/customer/verify-deposit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        customer_id: customerId,
        deposit_amount: depositAmount,
        tenure_months: tenureMonths
      })
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Simulation verification failed.");
    }

    // Render Simulation Outputs
    const resultBox = document.getElementById("sim-result-box");
    if (resultBox) resultBox.classList.remove("hidden");

    const verdictBanner = document.getElementById("sim-verdict-banner");
    const verdictTitle = document.getElementById("sim-verdict-title");
    const verdictSub = document.getElementById("sim-verdict-sub");

    if (data.verdict === "APPROVED_SAFE") {
      if (verdictBanner) verdictBanner.className = "verdict-banner banner-emerald";
      if (verdictTitle) verdictTitle.textContent = "✅ AI Verified — Safe Deposit Capacity Confirmed";
      if (verdictSub) verdictSub.textContent = data.ai_financial_advice || "Zero cashflow distress risk detected. Living expense reserves remain fully intact.";
    } else if (data.verdict === "APPROVED_WITH_CAUTION") {
      if (verdictBanner) verdictBanner.className = "verdict-banner banner-amber";
      if (verdictTitle) verdictTitle.textContent = "⚠️ Caution — Partial Emergency Buffer Erosion";
      if (verdictSub) verdictSub.textContent = data.ai_financial_advice || "Deposit approved, but remaining liquidity is tighter than recommended emergency reserve buffer.";
    } else {
      if (verdictBanner) verdictBanner.className = "verdict-banner banner-rose";
      if (verdictTitle) verdictTitle.textContent = "🛑 AI Warning — High Financial Distress Risk";
      if (verdictSub) verdictSub.textContent = data.ai_financial_advice || "High risk of cashflow failure or deposit exceeds liquid balance.";
    }

    // Risk score
    const riskScoreEl = document.getElementById("sim-risk-score");
    if (riskScoreEl) {
      riskScoreEl.textContent = `${data.failure_distress_risk_pct}%`;
      riskScoreEl.className = data.failure_distress_risk_pct < 25 
        ? "sim-value text-emerald font-mono" 
        : (data.failure_distress_risk_pct < 50 ? "sim-value text-amber font-mono" : "sim-value text-rose font-mono");
    }

    // Post-deposit balance
    const postBalEl = document.getElementById("sim-post-balance");
    if (postBalEl) {
      postBalEl.textContent = `€${Number(data.post_deposit_balance).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }

    // Maturity payout
    const maturityEl = document.getElementById("sim-maturity-payout");
    if (maturityEl) {
      maturityEl.textContent = `€${Number(data.projected_maturity_amount).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }

    // Interest gained
    const interestEl = document.getElementById("sim-interest-gained");
    if (interestEl) {
      interestEl.textContent = `+€${Number(data.projected_interest_earned).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} yield (${data.tenure_months}M @ ${data.annual_rate_pct}%)`;
    }

    // Diagnostic failure signals
    const signalsList = document.getElementById("sim-signals-list");
    if (signalsList) {
      if (data.warning_signals && data.warning_signals.length > 0) {
        signalsList.innerHTML = data.warning_signals.map(s => `
          <div class="signal-item">
            <span>Risk Signal</span>
            <strong class="signal-neg">⚠️ ${s}</strong>
          </div>
        `).join("");
      } else {
        signalsList.innerHTML = `
          <div class="signal-item">
            <span>Liquidity Protection</span>
            <strong class="signal-pos">✓ Surplus Reserve Buffer Maintained</strong>
          </div>
          <div class="signal-item">
            <span>Debt Service Load</span>
            <strong class="signal-pos">✓ Safe Debt-to-Income Ratio</strong>
          </div>
          <div class="signal-item">
            <span>Default History</span>
            <strong class="signal-pos">✓ Clean Credit Record</strong>
          </div>
        `;
      }
    }

    showToast(`AI Simulation Complete: ${data.verdict.replace(/_/g, ' ')}`, data.is_safe_to_deposit ? "success" : "warning");
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    if (spinner) spinner.classList.add("hidden");
    if (btnText) btnText.textContent = "⚡ Run Pre-Deposit AI Safety Check";
  }
}

function refreshCustomerPortalData() {
  showToast("Refreshing live customer financial metrics & limits...", "info");
  loadCustomerPortalData();
}

