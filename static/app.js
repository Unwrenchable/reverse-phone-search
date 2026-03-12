(function () {
  "use strict";

  /* ------------------------------------------------------------------ */
  /* Utility                                                              */
  /* ------------------------------------------------------------------ */
  function esc(str) {
    if (str == null) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  const form        = document.getElementById("search-form");
  const input       = document.getElementById("phone-input");
  const btn         = document.getElementById("search-btn");
  const resultArea  = document.getElementById("result-area");
  const inputError  = document.getElementById("input-error");

  /* ------------------------------------------------------------------ */
  /* Recent searches (localStorage, last 5)                              */
  /* ------------------------------------------------------------------ */
  const RECENT_KEY  = "rps_recent_searches";
  const RECENT_MAX  = 5;

  function loadRecent() {
    try { return JSON.parse(localStorage.getItem(RECENT_KEY) || "[]"); }
    catch { return []; }
  }

  function saveRecent(phone) {
    let list = loadRecent().filter(p => p !== phone);
    list.unshift(phone);
    if (list.length > RECENT_MAX) list = list.slice(0, RECENT_MAX);
    try { localStorage.setItem(RECENT_KEY, JSON.stringify(list)); } catch { /* quota */ }
    renderRecent(list);
  }

  function renderRecent(list) {
    const container = document.getElementById("recent-searches");
    const ul        = document.getElementById("recent-list");
    if (!list.length) { container.hidden = true; return; }
    ul.innerHTML = list.map(p =>
      `<button type="button" class="recent-chip" data-phone="${esc(p)}">${esc(p)}</button>`
    ).join("");
    container.hidden = false;
  }

  // Clicking a recent chip fills the input and submits
  document.getElementById("recent-list").addEventListener("click", function (e) {
    const chip = e.target.closest(".recent-chip");
    if (!chip) return;
    input.value = chip.dataset.phone;
    form.requestSubmit();
  });

  // Render saved searches on page load
  renderRecent(loadRecent());

  /* ------------------------------------------------------------------ */
  /* Client-side input validation                                        */
  /* ------------------------------------------------------------------ */
  // Allowed characters: digits, spaces, dashes, dots, parens, leading plus
  const PHONE_CHARS_RE = /^[+\d][\d\s\-().]*$/;

  function validateInput(value) {
    if (!value) return "Please enter a phone number.";
    const digitCount = (value.match(/\d/g) || []).length;
    if (!PHONE_CHARS_RE.test(value) || digitCount < 7) {
      return "Please enter a valid phone number (at least 7 digits; spaces, dashes, and parentheses are allowed).";
    }
    return "";
  }

  function setInputError(msg) {
    inputError.textContent = msg;
    input.setAttribute("aria-invalid", msg ? "true" : "false");
  }

  // Real-time validation on blur / while editing after first error
  let blurredOnce = false;
  input.addEventListener("blur", function () {
    blurredOnce = true;
    setInputError(validateInput(input.value.trim()));
  });
  input.addEventListener("input", function () {
    if (blurredOnce) setInputError(validateInput(input.value.trim()));
  });

  /* ------------------------------------------------------------------ */
  /* Form submit                                                          */
  /* ------------------------------------------------------------------ */
  form.addEventListener("submit", async function (e) {
    e.preventDefault();
    const phone = input.value.trim();

    const validationError = validateInput(phone);
    if (validationError) {
      blurredOnce = true;
      setInputError(validationError);
      input.focus();
      return;
    }
    setInputError("");

    btn.disabled = true;
    btn.innerHTML = '<span class="btn-icon">⏳</span> Searching…';
    resultArea.innerHTML = '<div class="loading"><span class="spinner"></span> Looking up number…</div>';

    try {
      const res  = await fetch("/search?" + new URLSearchParams({ phone }));
      const data = await res.json();

      if (res.status === 429) {
        showError(data.error || "Too many requests. Please wait a moment and try again.");
      } else if (!res.ok) {
        showError(data.error || "An unexpected error occurred.");
      } else if (data.found) {
        saveRecent(phone);
        showReport(data.result);
      } else {
        saveRecent(phone);
        showNotFound(phone);
      }
    } catch {
      showError("Could not reach the server. Please try again.");
    } finally {
      btn.disabled = false;
      btn.innerHTML = '<span class="btn-icon">🔍</span> Search';
    }
  });

  /* ------------------------------------------------------------------ */
  /* Report card                                                          */
  /* ------------------------------------------------------------------ */
  function showReport(r) {
    const spamScore  = Number(r.spam_score) || 0;
    const spamClass  = spamScore >= 70 ? "high" : spamScore >= 30 ? "medium" : "low";
    const spamBadge  = spamScore >= 70
      ? '<span class="badge badge-spam">⚠ Spam / Scam</span>'
      : spamScore >= 30
        ? '<span class="badge badge-warn">⚠ Suspicious</span>'
        : '<span class="badge badge-safe">✔ Safe</span>';

    const address = [r.address, r.city, r.state, r.zip].filter(Boolean).join(", ");

    resultArea.innerHTML = `
      <div class="report-card">

        <!-- Header -->
        <div class="report-header">
          <div class="avatar">${r.name ? r.name.charAt(0) : "?"}</div>
          <div class="report-header-info">
            <h2>${esc(r.name || "Unknown Caller")}</h2>
            <div class="report-phone">${esc(r.phone)}</div>
            ${spamBadge}
          </div>
        </div>

        <!-- Sections grid -->
        <div class="report-sections">

          <!-- Caller Info -->
          <div class="report-section">
            <h3>📞 Caller Info</h3>
            ${row("Line Type", r.line_type)}
            ${row("Carrier",   r.carrier)}
            ${row("Location",  r.city && r.state ? esc(r.city) + ", " + esc(r.state) : null)}
          </div>

          <!-- Owner Details -->
          <div class="report-section">
            <h3>👤 Owner Details</h3>
            ${row("Name",    r.name)}
            ${row("Age",     r.age != null ? r.age + " years old" : null)}
            ${row("Address", address || null)}
          </div>

          <!-- Contact Info -->
          <div class="report-section">
            <h3>✉ Contact Info</h3>
            ${row("Email",    r.email)}
            ${otherNumbersHtml(r.other_numbers)}
          </div>

          <!-- Employment -->
          <div class="report-section">
            <h3>💼 Employment</h3>
            ${row("Job Title", r.job_title)}
            ${row("Employer",  r.employer)}
          </div>

          <!-- Relatives -->
          <div class="report-section">
            <h3>👨‍👩‍👧 Possible Relatives</h3>
            ${tagList(r.relatives)}
          </div>

          <!-- Social Profiles -->
          <div class="report-section">
            <h3>🌐 Social Profiles</h3>
            ${socialHtml(r.social_facebook, "Facebook")}
            ${socialHtml(r.social_linkedin, "LinkedIn")}
            ${!r.social_facebook && !r.social_linkedin
              ? '<p style="color:var(--gray-400);font-size:.9rem">No profiles found</p>'
              : ""}
          </div>

          <!-- Spam Report — spans full width when it's the last odd item -->
          <div class="report-section" style="grid-column: 1 / -1">
            <h3>🛡 Spam Report</h3>
            <div class="spam-meter">
              <div class="spam-bar-bg">
                <div class="spam-bar-fill ${spamClass}" style="width:${spamScore}%"></div>
              </div>
              <span class="spam-label-text">
                Score: <strong>${spamScore}/100</strong>
                ${r.spam_label ? " &mdash; " + esc(r.spam_label) : ""}
              </span>
            </div>
          </div>

        </div>

        <!-- Footer row -->
        <div class="search-count-row">
          🔎 This number has been searched <strong>${Number(r.search_count).toLocaleString()}</strong> time(s)
        </div>
      </div>`;
  }

  /* ------------------------------------------------------------------ */
  /* Helpers                                                              */
  /* ------------------------------------------------------------------ */
  function row(label, value) {
    if (!value) return "";
    return `<div class="info-row">
              <span class="info-label">${esc(label)}</span>
              <span class="info-value">${esc(String(value))}</span>
            </div>`;
  }

  function tagList(items) {
    if (!items || !items.length) {
      return '<p style="color:var(--gray-400);font-size:.9rem">None on record</p>';
    }
    const tags = items.map(t => `<span class="tag">${esc(t)}</span>`).join("");
    return `<div class="tag-list">${tags}</div>`;
  }

  function otherNumbersHtml(numbers) {
    if (!numbers || !numbers.length) return "";
    const tags = numbers.map(n => `<span class="tag">${esc(n)}</span>`).join("");
    return `<div class="info-row" style="flex-direction:column">
              <span class="info-label" style="margin-bottom:.3rem">Other Numbers</span>
              <div class="tag-list">${tags}</div>
            </div>`;
  }

  /** Show social profile URL as plain text — no href/mailto link */
  function socialHtml(url, platform) {
    if (!url) return "";
    return `<div class="social-item">
              <span>${platform === "Facebook" ? "📘" : "💼"}</span>
              <span>${esc(platform)}: ${esc(url)}</span>
            </div>`;
  }

  function showNotFound(phone) {
    resultArea.innerHTML = `
      <div class="status-card">
        <div class="status-icon">🔎</div>
        <h2>No Record Found</h2>
        <p>We couldn't find any information for <strong>${esc(phone)}</strong>.<br>
           The number may be unlisted or not in our database.</p>
      </div>`;
  }

  function showError(msg) {
    resultArea.innerHTML = `
      <div class="status-card">
        <div class="status-icon">⚠️</div>
        <h2>Something Went Wrong</h2>
        <p>${esc(msg)}</p>
      </div>`;
  }

})();
