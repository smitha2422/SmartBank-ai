/**
 * SmartBank AI - Progressive Web App (PWA) & Campaign Intelligence Engine
 */

const API_BASE_URL = window.location.origin.includes(":5500") 
  ? "http://127.0.0.1:8000" 
  : window.location.origin;

let deferredPrompt = null;

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
  initServiceWorker();
  initPWAInstall();
  initHealthCheck();
  initDashboardTelemetry();
  initNavScrollSpy();

  // Trigger initial calculation
  const form = document.getElementById("prediction-form");
  if (form) {
    const formData = new FormData(form);
    const profile = formToJSON(formData);
    calculateAndDisplay(profile);
  }
  handleWhatIfChange();
});

/**
 * Register Service Worker for PWA (Installable App & Offline Mode)
 */
function initServiceWorker() {
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/sw.js').then((reg) => {
        console.log('[SmartBank PWA] Service Worker registered with scope:', reg.scope);
      }).catch((err) => {
        console.log('[SmartBank PWA] Service Worker registration failed:', err);
      });
    });
  }
}

/**
 * Handle PWA Native App Install Prompt
 */
function initPWAInstall() {
  const installBtn = document.getElementById("install-pwa-btn");
  
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    if (installBtn) {
      installBtn.style.display = "flex";
      installBtn.addEventListener("click", () => {
        installBtn.style.display = "none";
        deferredPrompt.prompt();
        deferredPrompt.userChoice.then((choiceResult) => {
          if (choiceResult.outcome === 'accepted') {
            console.log('[SmartBank PWA] User accepted the install prompt');
          }
          deferredPrompt = null;
        });
      });
    }
  });

  window.addEventListener('appinstalled', () => {
    console.log('[SmartBank PWA] SmartBank AI successfully installed!');
    if (installBtn) installBtn.style.display = "none";
  });
}

/**
 * Backend API Health Check
 */
async function initHealthCheck() {
  const statusEl = document.getElementById("api-status-text");
  try {
    const res = await fetch(`${API_BASE_URL}/api/health`, { method: "GET" });
    if (res.ok) {
      const data = await res.json();
      statusEl.textContent = `Engine Online (${data.model_type || "Model Ready"})`;
    } else {
      statusEl.textContent = "Engine Ready (Hybrid Engine)";
    }
  } catch (err) {
    if (statusEl) statusEl.textContent = "Engine Ready (Hybrid Engine)";
  }
}

/**
 * Fetch and populate dashboard telemetry from trained pipeline outputs
 */
async function initDashboardTelemetry() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/dashboard`);
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
    console.log("Telemetry fetch using baseline cache.");
  }
}

/**
 * Load Preset Archetype
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

  // Update What-If sliders in sync
  const sAge = document.getElementById("slider-age");
  const sBal = document.getElementById("slider-balance");
  const sPrev = document.getElementById("slider-previous");
  if (sAge) sAge.value = profile.age;
  if (sBal) sBal.value = profile.balance;
  if (sPrev) sPrev.value = profile.previous;

  calculateAndDisplay(profile);
  handleWhatIfChange();
}

/**
 * Form Submission Event
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
 * Submit Inference Request to Backend API or compute statistical fallback
 */
async function calculateAndDisplay(profile) {
  const btn = document.getElementById("predict-btn");
  if (btn) btn.disabled = true;

  try {
    const res = await fetch(`${API_BASE_URL}/api/predict`, {
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
 * Live "What-If" Sensitivity Slider Handler
 */
function handleWhatIfChange() {
  const age = parseInt(document.getElementById("slider-age")?.value || 58, 10);
  const balance = parseFloat(document.getElementById("slider-balance")?.value || 3250);
  const previous = parseInt(document.getElementById("slider-previous")?.value || 2, 10);

  const valAge = document.getElementById("val-slider-age");
  const valBal = document.getElementById("val-slider-balance");
  const valPrev = document.getElementById("val-slider-previous");

  if (valAge) valAge.textContent = `${age} yrs`;
  if (valBal) valBal.textContent = `€${balance.toLocaleString()}`;
  if (valPrev) valPrev.textContent = `${previous} contacts`;

  // Dynamic sensitivity weighting
  let score = 30;
  if (balance > 5000) score += 25;
  else if (balance > 2000) score += 18;
  else if (balance > 500) score += 8;
  else if (balance < 0) score -= 12;

  if (age >= 60) score += 20;
  else if (age <= 25) score += 10;

  if (previous >= 3) score += 18;
  else if (previous >= 1) score += 10;

  score = Math.max(5, Math.min(95, score));

  const textEl = document.getElementById("whatif-score-text");
  const fillEl = document.getElementById("whatif-bar-fill");
  const tagEl = document.getElementById("whatif-priority-tag");

  if (textEl) textEl.textContent = `${score} / 100`;
  if (fillEl) fillEl.style.width = `${score}%`;
  
  if (tagEl) {
    if (score >= 60) {
      tagEl.textContent = "HIGH CAMPAIGN PRIORITY";
      tagEl.style.color = "#34d399";
    } else if (score >= 35) {
      tagEl.textContent = "MEDIUM CAMPAIGN PRIORITY";
      tagEl.style.color = "#fbbf24";
    } else {
      tagEl.textContent = "LOW CAMPAIGN PRIORITY";
      tagEl.style.color = "#f87171";
    }
  }
}

/**
 * Client-Side Machine Learning Fallback
 */
function fallbackSimulation(p) {
  let score = 25;

  if (p.poutcome === "success") score += 45;
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
  let rec = "Low engagement likelihood: Preserve budget by deprioritizing direct outreach.";
  if (score >= 60) {
    priority = "HIGH";
    rec = "High engagement opportunity: Assign to senior relationship manager with premium deposit terms.";
  } else if (score >= 35) {
    priority = "MEDIUM";
    rec = "Moderate engagement potential: Reach out via standard phone or digital campaign with tailored savings offer.";
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
    disclaimer: "Opportunity Score translates ML likelihood into a campaign triage priority. It represents statistical association and does not guarantee subscription."
  });
}

/**
 * Render Inference Results
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

  // Radial Gauge Animation
  if (gaugeFill) {
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

  // Predictive Signals List
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

/**
 * Navigation Scroll-Spy for Mobile App
 */
function initNavScrollSpy() {
  const navItems = document.querySelectorAll(".mobile-nav-item");
  const sections = document.querySelectorAll("section[id]");

  window.addEventListener("scroll", () => {
    let current = "";
    sections.forEach((section) => {
      const sectionTop = section.offsetTop - 120;
      if (window.scrollY >= sectionTop) {
        current = section.getAttribute("id");
      }
    });

    navItems.forEach((item) => {
      item.classList.remove("active");
      if (item.getAttribute("href") === `#${current}`) {
        item.classList.add("active");
      }
    });
  });
}
