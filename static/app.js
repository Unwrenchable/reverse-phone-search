(function () {
  "use strict";

  const form       = document.getElementById("search-form");
  const input      = document.getElementById("phone-input");
  const btn        = document.getElementById("search-btn");
  const resultArea = document.getElementById("result-area");

  form.addEventListener("submit", async function (e) {
    e.preventDefault();
    const phone = input.value.trim();
    if (!phone) return;

    btn.disabled = true;
    btn.innerHTML = '<span class="btn-icon">⏳</span> Searching…';
    resultArea.innerHTML = '<div class="loading"><span class="spinner"></span> Looking up number…</div>';

    try {
      const res  = await fetch("/search?" + new URLSearchParams({ phone }));
      const data = await res.json();

      if (!res.ok) {
        showError(data.error || "An unexpected error occurred.");
      } else if (data.found) {
        showReport(data.result);
      } else {
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
        <button class="contribute-toggle-btn" id="contribute-toggle">
          ➕ Add This Number to the Database
        </button>
        <div class="contribute-form" id="contribute-form" hidden>
          <p class="contribute-desc">Help expand the database by contributing details for this number.</p>
          <form id="submit-form" novalidate>
            <input type="hidden" id="submit-phone" name="phone" value="${esc(phone)}" />
            <div class="form-row">
              <label for="submit-name">Name <span class="required">*</span></label>
              <input type="text" id="submit-name" name="name" placeholder="Full name" required />
            </div>
            <div class="form-row">
              <label for="submit-age">Age</label>
              <input type="number" id="submit-age" name="age" placeholder="e.g. 30" min="1" max="130" />
            </div>
            <div class="form-row">
              <label for="submit-carrier">Carrier</label>
              <input type="text" id="submit-carrier" name="carrier" placeholder="e.g. AT&amp;T, Verizon" />
            </div>
            <div class="form-row">
              <label for="submit-city">City</label>
              <input type="text" id="submit-city" name="city" placeholder="e.g. Chicago" />
            </div>
            <div class="form-row">
              <label for="submit-state">State</label>
              <input type="text" id="submit-state" name="state" placeholder="e.g. IL" maxlength="2" />
            </div>
            <div id="submit-error" class="form-error" hidden></div>
            <div class="form-actions">
              <button type="submit" id="submit-btn">Submit</button>
            </div>
          </form>
        </div>
      </div>`;

    document.getElementById("contribute-toggle").addEventListener("click", function () {
      const form = document.getElementById("contribute-form");
      const hidden = form.hidden;
      form.hidden = !hidden;
      this.textContent = hidden ? "✖ Cancel" : "➕ Add This Number to the Database";
    });

    document.getElementById("submit-form").addEventListener("submit", async function (e) {
      e.preventDefault();
      const errEl = document.getElementById("submit-error");
      errEl.hidden = true;

      const submitBtn = document.getElementById("submit-btn");
      submitBtn.disabled = true;
      submitBtn.textContent = "Submitting…";

      const payload = {
        phone:   document.getElementById("submit-phone").value,
        name:    document.getElementById("submit-name").value.trim(),
        age:     document.getElementById("submit-age").value   || undefined,
        carrier: document.getElementById("submit-carrier").value.trim() || undefined,
        city:    document.getElementById("submit-city").value.trim()    || undefined,
        state:   document.getElementById("submit-state").value.trim()   || undefined,
      };

      try {
        const res  = await fetch("/submit", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const data = await res.json();

        if (res.ok && data.added) {
          resultArea.innerHTML = `
            <div class="status-card">
              <div class="status-icon">✅</div>
              <h2>Number Added!</h2>
              <p>Thank you! <strong>${esc(payload.phone)}</strong> has been added to the database.</p>
            </div>`;
        } else {
          errEl.textContent = data.error || "Submission failed. Please try again.";
          errEl.hidden = false;
          submitBtn.disabled = false;
          submitBtn.textContent = "Submit";
        }
      } catch {
        errEl.textContent = "Could not reach the server. Please try again.";
        errEl.hidden = false;
        submitBtn.disabled = false;
        submitBtn.textContent = "Submit";
      }
    });
  }

  function showError(msg) {
    resultArea.innerHTML = `
      <div class="status-card">
        <div class="status-icon">⚠️</div>
        <h2>Something Went Wrong</h2>
        <p>${esc(msg)}</p>
      </div>`;
  }

  function esc(str) {
    if (str == null) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }
})();
