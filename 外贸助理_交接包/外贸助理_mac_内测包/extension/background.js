const BRIDGE_URL = "http://127.0.0.1:8765";

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (!message || message.type !== "bridgePost") {
    return false;
  }

  const path = message.path || "";
  const payload = message.payload || {};

  fetch(`${BRIDGE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
    .then(async (resp) => {
      const data = await resp.json().catch(() => ({}));
      if (!resp.ok) {
        sendResponse({
          ok: false,
          error: data.message || data.error || `HTTP ${resp.status}`,
        });
        return;
      }
      sendResponse({ ok: true, data });
    })
    .catch((err) => {
      sendResponse({ ok: false, error: err?.message || "bridge_fetch_failed" });
    });

  return true;
});
