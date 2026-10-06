/**
 * SmartBank AI - Frontend Logic & API Integration
 */

const API_BASE_URL = "http://127.0.0.1:8000";

// Preset archetypes for quick evaluation demo
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
    previous: 3
  },
  repeat_success: {
    age: 38,
    balance: 2900,
    job: "management",
    marital: "single",
    education: "tertiary",
    housing: "no",
    loan: "no",
    default: "no",
    poutcome: "success",
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
    previous: 0
  }
};

document.addEventListener("DOMContentLoaded", () => {
  initHealthCheck();
  initDashboardTelemetry();
  // Trigger initial calculation with default form values
  const form = document.getElementById("prediction-form");
  if (form) {
    const formData = new FormData(form);
    const profile = formToJSON(formData);
    calculateAndDisplay(profile);
  }
});

/**
 * Check Backend API Health
 */
async function initHealthCheck() {
  const statusEl = document.getElementById("api-status-text");
  try {
    const res = await fetch(`${API_BASE_URL}/health`, { method: "GET" });
    if (res.ok) {
      const data = await res.json();
      statusEl.textContent = `Engine Online (${data.model_type || "Model Active"})`;
    } else {
      statusEl.textContent = "Engine Offline (Using Local Simulation)";
    }
  } catch (err) {
    if (statusEl) statusEl.textContent = "Engine Offline (Using Local Simulation)";
  }
}

/**
 * Fetch and update dashboard KPIs from API
 */
async function initDashboardTelemetry() {
  try {
    const res = await fetch(`${API_BASE_URL}/dashboard`);
    if (res.ok) {
      const data = await res.json();
      if (data.metrics && data.metrics.unseen_test_performance) {
        const test = data.metrics.unseen_test_performance;
        const rocEl = document.getElementById("kpi-roc");
        const f1El = document.getElementById("kpi-f1");
        const modelEl = document.getElementById("kpi-model");
        if (rocEl) rocEl.textContent = test.roc_auc.toFixed(4);
        if (f1El) f1El.textContent = test.f1.toFixed(4);
        if (modelEl) modelEl.textContent = data.metrics.selected_model || "Random Forest";
      }
      if (data.eda && data.eda.rows) {
        const rowsEl = document.getElementById("kpi-rows");
        if (rowsEl) rowsEl.textContent = data.eda.rows.toLocaleString();
      }
    }
  } catch (e) {
    console.log("Telemetry fetch fallback to static benchmark.");
  }
}

/**
 * Load preset archetypes into form
 */
function loadPreset(key) {
  const profile = PRESETS[key];
  if (!profile) return;

  for (const [k, v] of Object.entries(profile)) {
    const input = document.getElementById(k);
    if (input) {
      input.value = v;
    }
  }

  calculateAndDisplay(profile);
}

/**
 * Handle form submission
 */
function handlePredict(event) {
  event.preventDefault();
  const form = event.target;
  const formData = new FormData(form);
  const profile = formToJSON(formData);
  calculateAndDisplay(profile);
}

function formToJSON(formData) {
  return {
    age: parseInt(formData.get("age"), 10) || 40,
    balance: parseFloat(formData.get("balance")) || 0,
    job: formData.get("job"),
    marital: formData.get("marital"),
    education: formData.get("education"),
    housing: formData.get("housing"),
    loan: formData.get("loan"),
    default: formData.get("default"),
    poutcome: formData.get("poutcome"),
    previous: parseInt(formData.get("previous"), 10) || 0
  };
}

/**
 * Submit to API or compute local simulation fallback
 */
async function calculateAndDisplay(profile) {
  const btn = document.getElementById("predict-btn");
  if (btn) btn.disabled = true;

  try {
    const res = await fetch(`${API_BASE_URL}/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(profile)
    });

    if (res.ok) {
      const data = await res.json();
      renderResults(data);
    } else {
      fallbackSimulation(profile);
    }
  } catch (err) {
    fallbackSimulation(profile);
  } finally {
    if (btn) btn.disabled = false;
  }
}

/**
 * Client-Side Model Simulation Fallback
 */
function fallbackSimulation(p) {
  // Approximate statistical weighting of pre-contact features
  let score = 25; // baseline

  if (p.poutcome === "success") score += 40;
  else if (p.poutcome === "failure") score += 5;
  
  if (p.housing === "no") score += 12;
  else score -= 8;
  
  if (p.loan === "yes") score -= 10;
  if (p.default === "yes") score -= 15;
  
  if (p.balance > 3000) score += 14;
  else if (p.balance > 1000) score += 6;
  else if (p.balance < 100) score -= 10;
  
  if (p.age >= 60) score += 15;
  else if (p.age <= 25) score += 8;
  
  if (p.previous >= 2) score += 8;
  if (p.education === "tertiary") score += 6;
  if (p.job === "retired" || p.job === "student") score += 10;
  if (p.job === "blue-collar") score -= 5;

  score = Math.max(5, Math.min(96, score));
  const prob = (score / 100).toFixed(4);

  let priority = "LOW";
  let rec = "Low engagement likelihood: Preserve bank budget by deprioritizing direct telephone outreach.";
  if (score >= 60) {
    priority = "HIGH";
    rec = "High engagement opportunity: Assign to senior relationship manager with premium deposit terms.";
  } else if (score >= 35) {
    priority = "MEDIUM";
    rec = "Moderate engagement potential: Reach out via standard phone/digital campaign with tailored savings offer.";
  }

  const signals = [];
  if (p.poutcome === "success") signals.push({ factor: "Previous Campaign Success", impact: "Strong Positive", type: "positive" });
  if (p.housing === "no") signals.push({ factor: "No Housing Loan Obligation", impact: "Positive", type: "positive" });
  if (p.balance > 2000) signals.push({ factor: "Healthy Account Balance (>€2,000)", impact: "Positive", type: "positive" });
  if (p.age >= 60) signals.push({ factor: "Retirement/Senior Demographics", impact: "Positive", type: "positive" });
  if (p.housing === "yes") signals.push({ factor: "Active Housing Loan Commitment", impact: "Restraining", type: "negative" });
  if (p.loan === "yes") signals.push({ factor: "Active Personal Loan Debt", impact: "Restraining", type: "negative" });
  if (!signals.length) signals.push({ factor: "Standard Demographic Baseline", impact: "Neutral", type: "neutral" });

  renderResults({
    opportunity_score: score,
    probability: parseFloat(prob),
    campaign_priority: priority,
    prediction_label: score >= 50 ? "Likely to Subscribe" : "Unlikely to Subscribe",
    recommendation: rec,
    predictive_signals: signals,
    disclaimer: "The Opportunity Score translates ML probability into a campaign prioritization signal. It represents statistical association and does not guarantee subscription."
  });
}

/**
 * Render Results on GUI
 */
function renderResults(res) {
  const scoreEl = document.getElementById("opp-score");
  const probEl = document.getElementById("raw-prob");
  const labelEl = document.getElementById("pred-label");
  const recEl = document.getElementById("rec-text");
  const badgeEl = document.getElementById("priority-badge");
  const listEl = document.getElementById("signals-list");
  const gaugeFill = document.getElementById("gauge-fill-circle");

  if (scoreEl) scoreEl.textContent = res.opportunity_score;
  if (probEl) probEl.textContent = Number(res.probability).toFixed(4);
  if (labelEl) labelEl.textContent = res.prediction_label;
  if (recEl) recEl.textContent = res.recommendation;

  // Priority Badge
  if (badgeEl) {
    badgeEl.textContent = `${res.campaign_priority} PRIORITY`;
    badgeEl.className = `badge priority-badge ${res.campaign_priority.toLowerCase()}`;
  }

  // Radial Gauge animation
  if (gaugeFill) {
    // Circumference for r=42 is 2 * PI * 42 ~= 263.89
    const circumference = 264;
    const offset = circumference - (res.opportunity_score / 100) * circumference;
    gaugeFill.style.strokeDashoffset = offset;
    
    if (res.campaign_priority === "HIGH") {
      gaugeFill.style.stroke = "#10b981";
    } else if (res.campaign_priority === "MEDIUM") {
      gaugeFill.style.stroke = "#f59e0b";
    } else {
      gaugeFill.style.stroke = "#ef4444";
    }
  }

  // Signals List
  if (listEl && res.predictive_signals) {
    listEl.innerHTML = "";
    res.predictive_signals.forEach(sig => {
      const li = document.createElement("li");
      li.className = `signal-item ${sig.type || "neutral"}`;
      li.textContent = `${sig.factor} (${sig.impact})`;
      listEl.appendChild(li);
    });
  }
}
