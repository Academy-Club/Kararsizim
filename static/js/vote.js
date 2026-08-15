document.addEventListener("DOMContentLoaded", () => {
  const page = document.querySelector(".poll-detail");
  if (!page) return;

  function getCsrfToken() {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? match[1] : "";
  }

  function showToast(message) {
    let container = document.querySelector(".toast-container");
    if (!container) {
      container = document.createElement("div");
      container.className = "toast-container";
      container.setAttribute("aria-live", "polite");
      document.body.appendChild(container);
    }
    const toast = document.createElement("div");
    toast.className = "toast";
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
  }

  function computeBadge(options, total) {
    if (total === 0) return "İlk oyu sen ver";
    if (options.length < 2) return "Karar net";
    const sorted = [...options].sort((a, b) => b.count - a.count);
    const diffPercent = (Math.abs(sorted[0].count - sorted[1].count) / total) * 100;
    if (diffPercent <= 5) return "Kalabalık da kararsız";
    if (diffPercent <= 20) return "Az farkla önde";
    return "Karar net";
  }

  function renderDecisionBar(options, total) {
    const bar = document.querySelector(".decision-bar");
    if (!bar) return;
    const badgeText = computeBadge(options, total);
    bar.setAttribute("aria-label", badgeText);
    bar.innerHTML = "";
    if (total > 0) {
      options.forEach((option, index) => {
        const segment = document.createElement("span");
        segment.className = "decision-bar__segment";
        segment.style.width = option.percent + "%";
        segment.style.background = "var(--opt-" + index + ")";
        bar.appendChild(segment);
      });
    }
    const badgeEl = document.querySelector(".poll-card__badge");
    if (badgeEl) badgeEl.textContent = badgeText;
  }

  function renderResults(data) {
    document.querySelectorAll(".poll-card__votes").forEach((el) => {
      el.textContent = data.total + " kişi oy verdi";
    });

    renderDecisionBar(data.options, data.total);

    const oldList = document.getElementById("option-list");
    if (!oldList) return;

    const newList = document.createElement("ul");
    newList.className = "option-list";
    newList.id = "option-list";
    newList.setAttribute("aria-live", "polite");

    data.options.forEach((option, index) => {
      const li = document.createElement("li");
      const row = document.createElement("div");
      row.className =
        "option-row option-row--results" +
        (option.id === data.voted_option_id ? " option-row--mine" : "");
      row.style.setProperty("--opt-color", "var(--opt-" + index + ")");

      const fill = document.createElement("span");
      fill.className = "option-row__fill";
      fill.style.width = option.percent + "%";
      fill.style.background = "var(--opt-" + index + ")";

      const label = document.createElement("span");
      label.className = "option-row__label";
      label.textContent = option.text + (option.id === data.voted_option_id ? " ✓" : "");

      const percent = document.createElement("span");
      percent.className = "option-row__percent";
      percent.textContent = "%" + option.percent;

      row.appendChild(fill);
      row.appendChild(label);
      row.appendChild(percent);
      li.appendChild(row);
      newList.appendChild(li);
    });

    oldList.replaceWith(newList);
  }

  page.addEventListener("submit", (event) => {
    const form = event.target.closest(".option-vote-form");
    if (!form) return;
    event.preventDefault();

    const buttons = page.querySelectorAll(".option-vote-form button");
    buttons.forEach((button) => {
      button.disabled = true;
    });

    fetch(form.action, {
      method: "POST",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": getCsrfToken(),
      },
      body: new FormData(form),
    })
      .then((response) => response.json().then((data) => ({ ok: response.ok, data })))
      .then(({ ok, data }) => {
        if (!ok && data.error) {
          showToast(data.error);
        }
        if (data.options) {
          renderResults(data);
        } else {
          buttons.forEach((button) => {
            button.disabled = false;
          });
        }
      })
      .catch(() => {
        showToast("Bağlantı hatası, tekrar dene.");
        buttons.forEach((button) => {
          button.disabled = false;
        });
      });
  });
});
