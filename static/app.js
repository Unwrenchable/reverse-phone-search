(function () {
  "use strict";

  const form = document.getElementById("search-form");
  const input = document.getElementById("phone-input");
  const btn = document.getElementById("search-btn");
  const resultArea = document.getElementById("result-area");

  form.addEventListener("submit", async function (e) {
    e.preventDefault();
    const phone = input.value.trim();
    if (!phone) return;

    btn.disabled = true;
    btn.textContent = "Searching…";
    resultArea.innerHTML = "";

    try {
      const res = await fetch("/search?" + new URLSearchParams({ phone }));
      const data = await res.json();

      if (!res.ok) {
        showError(data.error || "An unexpected error occurred.");
      } else if (data.found) {
        showResult(data.result);
      } else {
        showNotFound(phone);
      }
    } catch {
      showError("Could not reach the server. Please try again.");
    } finally {
      btn.disabled = false;
      btn.textContent = "Search";
    }
  });

  function showResult(r) {
    const rows = [
      ["Name", escHtml(r.name)],
      ["Phone", escHtml(r.phone)],
      ["Address", escHtml([r.address, r.city, r.state].filter(Boolean).join(", "))],
      ["Email", r.email ? `<a href="mailto:${escHtml(r.email)}">${escHtml(r.email)}</a>` : "—"],
    ];

    const tbody = rows
      .map(([label, val]) => `<tr><td>${escHtml(label)}</td><td>${val || "—"}</td></tr>`)
      .join("");

    resultArea.innerHTML = `
      <div class="result-card success">
        <h2>✅ Record Found</h2>
        <table class="result-table"><tbody>${tbody}</tbody></table>
      </div>`;
  }

  function showNotFound(phone) {
    resultArea.innerHTML = `
      <div class="result-card not-found">
        <p class="message">No record found for <strong>${escHtml(phone)}</strong>.</p>
      </div>`;
  }

  function showError(msg) {
    resultArea.innerHTML = `
      <div class="result-card error">
        <p class="message error">⚠️ ${escHtml(msg)}</p>
      </div>`;
  }

  function escHtml(str) {
    if (str == null) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }
})();
