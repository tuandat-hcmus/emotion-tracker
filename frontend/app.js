const storageKeys = {
  backendUrl: "emotion-backend-url",
  token: "emotion-access-token",
  user: "emotion-user",
};

const state = {
  backendUrl: localStorage.getItem(storageKeys.backendUrl) || "http://127.0.0.1:8000",
  token: localStorage.getItem(storageKeys.token) || "",
  user: safeJsonParse(localStorage.getItem(storageKeys.user)),
  calendarDays: 14,
  wrapupType: "weekly",
};

const elements = {
  backendUrl: document.querySelector("#backend-url"),
  saveBackend: document.querySelector("#save-backend"),
  refreshAll: document.querySelector("#refresh-all"),
  sessionStatus: document.querySelector("#session-status"),
  showLogin: document.querySelector("#show-login"),
  showRegister: document.querySelector("#show-register"),
  loginForm: document.querySelector("#login-form"),
  registerForm: document.querySelector("#register-form"),
  logout: document.querySelector("#logout"),
  homeCards: document.querySelector("#home-cards"),
  previewForm: document.querySelector("#preview-form"),
  previewOutput: document.querySelector("#preview-output"),
  calendarGrid: document.querySelector("#calendar-grid"),
  calendarToolbar: document.querySelectorAll("[data-days]"),
  weeklyWrapup: document.querySelector("#weekly-wrapup"),
  monthlyWrapup: document.querySelector("#monthly-wrapup"),
  wrapupOutput: document.querySelector("#wrapup-output"),
  crisisForm: document.querySelector("#crisis-form"),
  crisisOutput: document.querySelector("#crisis-output"),
  cardTemplate: document.querySelector("#card-template"),
};

initialize();

function initialize() {
  elements.backendUrl.value = state.backendUrl;
  wireEvents();
  renderSession();
  renderPlaceholderCards();
  renderEmptyCalendar();
  loadCrisisResources("US");
  if (state.token) {
    refreshDashboard();
  }
}

function wireEvents() {
  elements.saveBackend.addEventListener("click", () => {
    state.backendUrl = elements.backendUrl.value.trim().replace(/\/$/, "");
    localStorage.setItem(storageKeys.backendUrl, state.backendUrl);
    renderSession("Backend URL updated.");
  });

  elements.refreshAll.addEventListener("click", () => refreshDashboard());
  elements.showLogin.addEventListener("click", () => toggleAuthMode("login"));
  elements.showRegister.addEventListener("click", () => toggleAuthMode("register"));
  elements.logout.addEventListener("click", clearSession);
  elements.loginForm.addEventListener("submit", handleLogin);
  elements.registerForm.addEventListener("submit", handleRegister);
  elements.previewForm.addEventListener("submit", handlePreview);
  elements.crisisForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const country = new FormData(elements.crisisForm).get("country")?.toString().trim() || "US";
    loadCrisisResources(country);
  });
  elements.calendarToolbar.forEach((button) => {
    button.addEventListener("click", () => {
      state.calendarDays = Number(button.dataset.days);
      updateChipState(elements.calendarToolbar, button);
      loadCalendar();
    });
  });
  elements.weeklyWrapup.addEventListener("click", () => {
    state.wrapupType = "weekly";
    updateChipState([elements.weeklyWrapup, elements.monthlyWrapup], elements.weeklyWrapup);
    loadWrapup();
  });
  elements.monthlyWrapup.addEventListener("click", () => {
    state.wrapupType = "monthly";
    updateChipState([elements.weeklyWrapup, elements.monthlyWrapup], elements.monthlyWrapup);
    loadWrapup();
  });
}

async function handleLogin(event) {
  event.preventDefault();
  const formData = new FormData(elements.loginForm);
  try {
    const payload = await apiFetch("/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({
        email: formData.get("email"),
        password: formData.get("password"),
      }),
    });
    setSession(payload.access_token, payload.user);
    renderSession(`Logged in as ${payload.user.email}.`);
    refreshDashboard();
  } catch (error) {
    renderSession(error.message, true);
  }
}

async function handleRegister(event) {
  event.preventDefault();
  const formData = new FormData(elements.registerForm);
  try {
    await apiFetch("/v1/auth/register", {
      method: "POST",
      body: JSON.stringify({
        display_name: normalizeOptionalText(formData.get("display_name")),
        email: formData.get("email"),
        password: formData.get("password"),
      }),
    });
    toggleAuthMode("login");
    renderSession("Account created. Log in with the same credentials.");
  } catch (error) {
    renderSession(error.message, true);
  }
}

async function handlePreview(event) {
  event.preventDefault();
  if (!requireSession()) {
    return;
  }

  const formData = new FormData(elements.previewForm);
  const topicInput = normalizeOptionalText(formData.get("override_topic_tags"));
  const body = {
    transcript: formData.get("transcript"),
    override_risk_level: normalizeOptionalText(formData.get("override_risk_level")),
    override_topic_tags: topicInput ? topicInput.split(",").map((item) => item.trim()).filter(Boolean) : null,
  };

  elements.previewOutput.textContent = "Generating preview...";
  try {
    const payload = await apiFetch("/v1/me/respond-preview", {
      method: "POST",
      body: JSON.stringify(body),
      auth: true,
    });
    elements.previewOutput.innerHTML = `
      <strong>${escapeHtml(payload.emotion_analysis.emotion_label || "No dominant label")} · risk ${escapeHtml(payload.risk_level)}</strong>
      <p>${escapeHtml(payload.ai_response)}</p>
      <p><strong>Plan:</strong> ${escapeHtml(payload.response_plan.tone)}, ${escapeHtml(payload.response_plan.acknowledgment_focus)}</p>
      <p><strong>Signals:</strong> ${escapeHtml(payload.emotion_analysis.dominant_signals.join(", ") || "none")}</p>
      <p><strong>Topics:</strong> ${escapeHtml(payload.topic_tags.join(", ") || "none")}</p>
      ${payload.gentle_suggestion ? `<p><strong>Suggestion:</strong> ${escapeHtml(payload.gentle_suggestion)}</p>` : ""}
      ${payload.quote ? `<p><strong>Quote:</strong> ${escapeHtml(payload.quote.short_text)}</p>` : ""}
    `;
  } catch (error) {
    elements.previewOutput.textContent = error.message;
  }
}

async function refreshDashboard() {
  if (!requireSession()) {
    return;
  }

  renderSession("Refreshing dashboard...");
  await Promise.allSettled([loadHome(), loadCalendar(), loadWrapup(), loadMe()]);
}

async function loadMe() {
  try {
    const me = await apiFetch("/v1/me", { auth: true });
    state.user = me;
    localStorage.setItem(storageKeys.user, JSON.stringify(me));
    renderSession(`Active session: ${me.email}`);
  } catch (error) {
    renderSession(error.message, true);
  }
}

async function loadHome() {
  elements.homeCards.innerHTML = "";
  try {
    const payload = await apiFetch("/v1/me/home", { auth: true });
    const cards = [
      {
        label: "Today",
        value: `${payload.today.total_entries_today} entries`,
        meta: `${payload.today.session_types_present.join(", ") || "No check-ins yet"} · latest ${payload.today.latest_emotion_label || "n/a"}`,
      },
      {
        label: "Tree",
        value: `${payload.tree.vitality_score} vitality`,
        meta: `${payload.tree.current_stage || "No stage yet"} · streak ${payload.tree.streak_days} days`,
      },
      {
        label: "Trend",
        value: payload.recent_trend.last_7_days_average_valence ?? "n/a",
        meta: `${payload.recent_trend.entries_last_7_days} entries over the last 7 days`,
      },
      {
        label: "Quote",
        value: payload.quote?.short_text || "Opted out",
        meta: payload.quote ? `${payload.quote.tone} · ${payload.quote.source_type}` : "Quotes disabled in preferences",
      },
      {
        label: "Goal",
        value: `${payload.preferences_summary.checkin_goal_per_day}/day`,
        meta: `Reminder ${payload.preferences_summary.reminder_enabled ? "on" : "off"} · tree ${payload.preferences_summary.preferred_tree_type}`,
      },
      {
        label: "Wrap-ups",
        value: payload.latest_wrapup_meta.latest_weekly_wrapup_at ? "Generated" : "Pending",
        meta: `Weekly ${payload.latest_wrapup_meta.latest_weekly_wrapup_at || "none"} · Monthly ${payload.latest_wrapup_meta.latest_monthly_wrapup_at || "none"}`,
      },
    ];
    cards.forEach(renderCard);
  } catch (error) {
    elements.homeCards.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  }
}

async function loadCalendar() {
  if (!state.token) {
    return;
  }
  elements.calendarGrid.innerHTML = `<div class="empty-state">Loading ${state.calendarDays}-day calendar...</div>`;
  try {
    const payload = await apiFetch(`/v1/me/calendar?days=${state.calendarDays}`, { auth: true });
    elements.calendarGrid.innerHTML = payload.items
      .map((item) => {
        return `
          <article class="calendar-day mood-${escapeHtml(item.mood_color_token)}">
            <h3>${escapeHtml(item.date)}</h3>
            <p><strong>${item.entry_count}</strong> entries</p>
            <p>${escapeHtml(item.primary_emotion_label || "No primary emotion")}</p>
            <p>${escapeHtml(item.topic_tags_top.join(", ") || "No topics")}</p>
          </article>
        `;
      })
      .join("");
  } catch (error) {
    elements.calendarGrid.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  }
}

async function loadWrapup() {
  if (!state.token) {
    return;
  }
  elements.wrapupOutput.textContent = `Loading ${state.wrapupType} wrap-up...`;
  const path = state.wrapupType === "weekly" ? "/v1/me/wrapups/weekly/latest" : "/v1/me/wrapups/monthly/latest";
  try {
    const payload = await apiFetch(path, { auth: true });
    elements.wrapupOutput.innerHTML = `
      <strong>${escapeHtml(payload.payload.period_type)} · ${escapeHtml(payload.period_start)} to ${escapeHtml(payload.period_end)}</strong>
      <p>${escapeHtml(payload.payload.closing_message)}</p>
      <ul class="list-reset">
        <li><strong>Total entries:</strong> ${escapeHtml(String(payload.payload.total_entries))}</li>
        <li><strong>Check-in days:</strong> ${escapeHtml(String(payload.payload.total_checkin_days))}</li>
        <li><strong>Top topics:</strong> ${escapeHtml(payload.payload.top_topics.join(", ") || "none")}</li>
        <li><strong>Notable shift:</strong> ${escapeHtml(payload.payload.notable_shift)}</li>
      </ul>
    `;
  } catch (error) {
    elements.wrapupOutput.textContent = error.message;
  }
}

async function loadCrisisResources(country) {
  elements.crisisOutput.textContent = "Loading resources...";
  try {
    const payload = await apiFetch(`/v1/resources/crisis?country=${encodeURIComponent(country)}`);
    elements.crisisOutput.innerHTML = `
      <strong>${escapeHtml(payload.country)}</strong>
      <ul class="list-reset">
        <li><strong>Emergency:</strong> ${escapeHtml(payload.emergency_contacts.join(", ") || "n/a")}</li>
        <li><strong>Hotlines:</strong> ${escapeHtml(payload.crisis_hotlines.join(" | "))}</li>
        <li><strong>Notes:</strong> ${escapeHtml(payload.notes.join(" "))}</li>
      </ul>
    `;
  } catch (error) {
    elements.crisisOutput.textContent = error.message;
  }
}

function apiFetch(path, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };
  if (options.auth && state.token) {
    headers.Authorization = `Bearer ${state.token}`;
  }

  return fetch(`${state.backendUrl}${path}`, {
    method: options.method || "GET",
    headers,
    body: options.body,
  }).then(async (response) => {
    const isJson = response.headers.get("content-type")?.includes("application/json");
    const payload = isJson ? await response.json() : null;
    if (!response.ok) {
      const detail = payload?.error?.message || payload?.detail || `Request failed with status ${response.status}`;
      throw new Error(detail);
    }
    return payload;
  });
}

function setSession(token, user) {
  state.token = token;
  state.user = user;
  localStorage.setItem(storageKeys.token, token);
  localStorage.setItem(storageKeys.user, JSON.stringify(user));
}

function clearSession() {
  state.token = "";
  state.user = null;
  localStorage.removeItem(storageKeys.token);
  localStorage.removeItem(storageKeys.user);
  renderSession("Session cleared.");
  renderPlaceholderCards();
  renderEmptyCalendar();
  elements.wrapupOutput.textContent = "No wrap-up loaded yet.";
  elements.previewOutput.textContent = "Preview output will appear here after login.";
}

function renderSession(message, isError = false) {
  const userLine = state.user?.email ? `Signed in as ${state.user.email}.` : "No active session.";
  elements.sessionStatus.textContent = message || userLine;
  elements.sessionStatus.style.color = isError ? "var(--danger)" : "var(--muted)";
}

function renderPlaceholderCards() {
  elements.homeCards.innerHTML = "";
  [
    ["Today", "Login required", "Home cards populate from /v1/me/home."],
    ["Tree", "No data", "Vitality, streak, and current stage appear here."],
    ["Trend", "No data", "Last-7-day averages appear here."],
    ["Quote", "No data", "Optional quote will appear here."],
  ].forEach(([label, value, meta]) => renderCard({ label, value, meta }));
}

function renderEmptyCalendar() {
  elements.calendarGrid.innerHTML = `<div class="empty-state">Calendar loads after login.</div>`;
}

function renderCard({ label, value, meta }) {
  const fragment = elements.cardTemplate.content.cloneNode(true);
  fragment.querySelector(".card-label").textContent = label;
  fragment.querySelector(".card-value").textContent = value;
  fragment.querySelector(".card-meta").textContent = meta;
  elements.homeCards.appendChild(fragment);
}

function requireSession() {
  if (state.token) {
    return true;
  }
  renderSession("Log in first to use authenticated endpoints.", true);
  return false;
}

function toggleAuthMode(mode) {
  const loginMode = mode === "login";
  elements.loginForm.classList.toggle("hidden", !loginMode);
  elements.registerForm.classList.toggle("hidden", loginMode);
  elements.showLogin.classList.toggle("chip-active", loginMode);
  elements.showRegister.classList.toggle("chip-active", !loginMode);
}

function updateChipState(chips, activeChip) {
  chips.forEach((chip) => chip.classList.toggle("chip-active", chip === activeChip));
}

function normalizeOptionalText(value) {
  const normalized = value?.toString().trim();
  return normalized ? normalized : null;
}

function safeJsonParse(value) {
  if (!value) {
    return null;
  }
  try {
    return JSON.parse(value);
  } catch {
    return null;
  }
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
