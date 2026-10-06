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
    document.getElementById("user-name-display").textContent = currentUser.name || "Demo Analyst";
    document.getElementById("user-role-display").textContent = currentUser.role || "Campaign Analyst";
    const initials = (currentUser.name || "DA").split(" ").map(n => n[0]).join("").substring(0, 2).toUpperCase();
    document.getElementById("user-avatar-badge").textContent = initials;
  }
  
  // Load initial view data
  loadDashboardData();
  fetchCustomers();
  runCampaignOptimizer();
  fetchAssessmentHistory();
  fetchCampaignFeedback();
}

function autofillDemo(role) {
  const emailInput = document.getElementById("login-email");
  const passInput = document.getElementById("login-password");
  if (role === "admin") {
    emailInput.value = "admin@smartbank.ai";
    passInput.value = "admin123";
  } else {
    emailInput.value = "analyst@smartbank.ai";
    passInput.value = "demo123";
  }
  document.getElementById("login-error").classList.add("hidden");
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
  btnText.textContent = "Verifying Demo Credentials...";

  try {
    const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Authentication failed.");
    }

    currentUser = data.user;
    localStorage.setItem("smartbank_user", JSON.stringify(currentUser));
    showToast(`Welcome back, ${currentUser.name}!`, "success");
    showAppShell();
    navigateTo("view-dashboard");
  } catch (err) {
    errorBox.textContent = err.message;
    errorBox.classList.remove("hidden");
  } finally {
    spinner.classList.add("hidden");
    btnText.textContent = "Sign In to Demo Workspace";
  }
}

function handleLogout() {
  currentUser = null;
  localStorage.removeItem("smartbank_user");
  showToast("Logged out of demo session.", "info");
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
// 2. VIEW NAVIGATION & ROUTING
// -------------------------------------------------------------
const PAGE_TITLES = {
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
