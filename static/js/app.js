const modal = document.querySelector("[data-modal]");
const closeBtn = document.querySelector("[data-close]");

if (modal && closeBtn) {
  closeBtn.addEventListener("click", () => {
    modal.remove();
  });
}

const weatherKey = document.body.getAttribute("data-weather") || "default";
const safeKey = weatherKey.toLowerCase().trim();
document.body.setAttribute("data-weather", safeKey);

const weatherTimeEl = document.querySelector("[data-weather-time]");
if (weatherTimeEl) {
  const unix = Number(weatherTimeEl.dataset.unix || "0");
  const tz = Number(weatherTimeEl.dataset.tz || "0");
  if (!Number.isNaN(unix) && !Number.isNaN(tz) && unix > 0) {
    const baseMs = (unix + tz) * 1000;
    const startedAt = Date.now();

    const formatTime = (ms) => {
      const d = new Date(ms);
      const options = {
        month: "short",
        day: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        hour12: true,
      };
      return d.toLocaleString(undefined, options);
    };

    const tick = () => {
      const nowMs = baseMs + (Date.now() - startedAt);
      weatherTimeEl.textContent = `Local time: ${formatTime(nowMs)}`;
    };

    tick();
    setInterval(tick, 1000);
  }
}

const toastMessages = document.querySelectorAll(".messages.toast .message");
if (toastMessages.length) {
  setTimeout(() => {
    toastMessages.forEach((msg) => msg.classList.add("hide"));
  }, 4000);
}
