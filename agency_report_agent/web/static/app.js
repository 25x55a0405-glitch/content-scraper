// Report Desk — small progressive enhancements. Everything works without this file.
(function () {
  // Ask before destructive or replacing actions.
  document.addEventListener("submit", function (e) {
    var btn = e.submitter || e.target.querySelector("[data-confirm]");
    var msg = btn && btn.getAttribute && btn.getAttribute("data-confirm");
    if (msg && !window.confirm(msg)) { e.preventDefault(); return; }
    // Prevent double submits (double approvals, double uploads).
    var form = e.target;
    if (form.dataset.sent) { e.preventDefault(); return; }
    form.dataset.sent = "1";
    if (btn && btn.tagName === "BUTTON") { setTimeout(function () { btn.disabled = true; }, 0); }
  });

  // Keep the colour picker and its text box in step.
  document.querySelectorAll("input[type=color][data-sync]").forEach(function (picker) {
    var text = document.getElementById(picker.dataset.sync);
    if (!text) return;
    picker.addEventListener("input", function () { text.value = picker.value.toUpperCase(); });
    text.addEventListener("input", function () { if (/^#[0-9a-fA-F]{6}$/.test(text.value)) picker.value = text.value; });
  });

  // While something is drafting, poll and reload when it's done.
  var body = document.body;
  var url = body.dataset.poll;
  if (url) {
    var key = body.dataset.pollKey, whileVal = body.dataset.pollWhile;
    var tick = function () {
      fetch(url, { credentials: "same-origin", headers: { Accept: "application/json" } })
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (d) {
          if (!d) return;
          var v = d[key];
          var busy = whileVal ? v === whileVal : v > 0;
          if (!busy) { window.location.reload(); } else { setTimeout(tick, 2500); }
        })
        .catch(function () { setTimeout(tick, 5000); });
    };
    setTimeout(tick, 2500);
  }
})();
