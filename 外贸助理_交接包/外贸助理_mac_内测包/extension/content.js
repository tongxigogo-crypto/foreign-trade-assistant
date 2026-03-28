(() => {
  const ACTION_TAG_REGEX = /<action>([\s\S]*?)<\/action>/g;
  const ONBOARDING_KEY = "ta_onboarding_seen_v2";
  const SETTINGS_KEY = "ta_settings_v1";
  const DEFAULT_SETTINGS = {
    appendResultToInput: false,
    openDashboardAfterExecute: false,
    autoSyncConversation: true,
    templateLang: "zh",
    templateMode: "standard",
    customInstruction: "",
    launcherHidden: false,
    launcherPos: null,
  };

  let activeEditable = null;
  let hintChip = null;
  let actionPanel = null;
  let launcherWrap = null;
  let launcherBtn = null;
  let launcherRestoreBtn = null;
  let actionScanTimer = null;
  let conversationSyncTimer = null;
  let actionExecuting = false;
  let actionBaselineReady = false;
  let runtimeSettings = { ...DEFAULT_SETTINGS };
  let lastSyncedHash = "";
  let lastSyncedAt = 0;
  let lastSyncStatus = "未同步";

  const processedActionCounts = new Map();
  const pendingActions = [];

  const isEditable = (el) => {
    if (!el) return false;
    if (el.tagName === "TEXTAREA") return true;
    if (el.tagName === "INPUT") return ["text", "search"].includes((el.type || "text").toLowerCase());
    return Boolean(el.isContentEditable);
  };

  const isLikelyChatComposer = (el) => {
    if (!isEditable(el)) return false;
    const text = [
      el.getAttribute?.("placeholder") || "",
      el.getAttribute?.("aria-label") || "",
      el.getAttribute?.("data-placeholder") || "",
      el.id || "",
      el.name || "",
      el.className || "",
    ].join(" ").toLowerCase();
    const include = ["message", "chat", "prompt", "ask", "输入", "提问", "对话", "发送"];
    const exclude = ["search", "model", "mode", "filter", "setting", "设置", "模型", "模式", "筛选"];
    const includeHit = include.some((k) => text.includes(k));
    const excludeHit = exclude.some((k) => text.includes(k));
    if (includeHit && !excludeHit) return true;
    const rect = el.getBoundingClientRect?.();
    return Boolean(rect && rect.width >= 280 && rect.bottom >= window.innerHeight * 0.55);
  };

  const getEditable = (node) => {
    if (!node) return null;
    const start = node.nodeType === Node.TEXT_NODE ? node.parentElement : node;
    if (!start) return null;
    if (isLikelyChatComposer(start)) return start;
    const found = start.closest?.('textarea,input,[contenteditable="true"],[contenteditable=""],[contenteditable]') || null;
    return isLikelyChatComposer(found) ? found : null;
  };

  const findAnyEditable = () => {
    const nodes = Array.from(
      document.querySelectorAll('textarea,input[type="text"],input[type="search"],[contenteditable="true"],[contenteditable=""],[contenteditable]')
    );
    return nodes.find((n) => isLikelyChatComposer(n)) || null;
  };

  const getValue = (el) => (el?.tagName === "TEXTAREA" || el?.tagName === "INPUT" ? el.value || "" : el?.innerText || "");
  const setValue = (el, value) => {
    if (!el) return;
    if (el.tagName === "TEXTAREA" || el.tagName === "INPUT") {
      el.value = value;
      el.dispatchEvent(new Event("input", { bubbles: true }));
      return;
    }
    el.innerText = value;
    el.dispatchEvent(new Event("input", { bubbles: true }));
  };

  const modelName = () => {
    const host = location.hostname.toLowerCase();
    if (host.includes("doubao")) return "doubao-web";
    if (host.includes("deepseek")) return "deepseek-web";
    if (host.includes("gemini") || host.includes("google.com")) return "gemini-web";
    if (host.includes("qwen") || host.includes("aliyun")) return "qwen-web";
    return "web-llm";
  };

  const bridgePost = (path, payload) =>
    new Promise((resolve, reject) => {
      chrome.runtime.sendMessage({ type: "bridgePost", path, payload: payload || {} }, (response) => {
        if (chrome.runtime.lastError) return reject(new Error(chrome.runtime.lastError.message || "runtime_message_failed"));
        if (!response) return reject(new Error("empty_response_from_background"));
        if (!response.ok) return reject(new Error(response.error || "bridge_request_failed"));
        resolve(response.data || {});
      });
    });

  const saveSettings = (patch) =>
    new Promise((resolve) => {
      runtimeSettings = { ...runtimeSettings, ...patch };
      chrome.storage.local.set({ [SETTINGS_KEY]: runtimeSettings }, () => resolve(runtimeSettings));
    });

  const loadSettings = () =>
    new Promise((resolve) => {
      chrome.storage.local.get([SETTINGS_KEY], (res) => {
        runtimeSettings = { ...DEFAULT_SETTINGS, ...(res?.[SETTINGS_KEY] || {}) };
        resolve(runtimeSettings);
      });
    });

  const clearHintChip = () => {
    hintChip?.remove();
    hintChip = null;
  };

  const showHintChip = () => {
    clearHintChip();
    if (!activeEditable) return;
    const rect = activeEditable.getBoundingClientRect();
    hintChip = document.createElement("div");
    hintChip.className = "ta-hint-chip";
    hintChip.style.left = `${Math.max(12, rect.left)}px`;
    hintChip.style.top = `${Math.max(12, rect.bottom + 8)}px`;
    hintChip.innerHTML = `<span>检测到 @，可注入本地胶囊</span><button data-action="inject">注入</button><button data-action="close">关闭</button>`;
    hintChip.addEventListener("click", async (e) => {
      const action = e.target?.getAttribute?.("data-action");
      if (action === "close") return clearHintChip();
      if (action === "inject") {
        clearHintChip();
        await buildAndPreviewCapsule();
      }
    });
    document.body.appendChild(hintChip);
  };

  const showCapsuleModal = (capsule) => {
    const mask = document.createElement("div");
    mask.className = "ta-modal-mask";
    const mentions = (capsule.visible_mentions || []).map((x) => `<code>${x}</code>`).join(" ") || "无";
    const facts = (capsule.facts || []).slice(0, 8).map((x) => `<li>${x}</li>`).join("") || "<li>无</li>";
    mask.innerHTML = `
      <div class="ta-modal">
        <h3>本地胶囊预览</h3>
        <div class="ta-meta"><strong>召回标签：</strong>${mentions}</div>
        <div class="ta-meta"><strong>关键事实：</strong><ul>${facts}</ul></div>
        <div class="ta-meta"><strong>最终注入 Prompt：</strong></div>
        <div class="ta-prompt-box">${(capsule.injected_prompt || "").replaceAll("<", "&lt;")}</div>
        <div class="ta-actions"><button class="ta-primary" data-action="confirm">确认注入</button><button data-action="cancel">取消</button></div>
      </div>`;
    mask.addEventListener("click", (e) => {
      if (e.target === mask) mask.remove();
    });
    mask.querySelectorAll("button").forEach((btn) => {
      btn.addEventListener("click", () => {
        if (btn.getAttribute("data-action") === "confirm") {
          if (!activeEditable || !isLikelyChatComposer(activeEditable)) activeEditable = findAnyEditable();
          if (activeEditable) setValue(activeEditable, capsule.injected_prompt || getValue(activeEditable));
        }
        mask.remove();
      });
    });
    document.body.appendChild(mask);
  };

  const buildAndPreviewCapsule = async () => {
    if (!activeEditable || !isLikelyChatComposer(activeEditable)) activeEditable = findAnyEditable();
    if (!activeEditable) {
      window.alert("未找到聊天输入框，请先点击对话输入区域。");
      return;
    }
    try {
      const payload = {
        user_input: getValue(activeEditable),
        model_name: modelName(),
        template_lang: runtimeSettings.templateLang || "zh",
        template_mode: runtimeSettings.templateMode || "standard",
        custom_instruction: runtimeSettings.customInstruction || "",
      };
      const data = await bridgePost("/capsule/build", payload);
      showCapsuleModal(data.capsule || {});
    } catch (err) {
      window.alert(`本地桥接服务不可用：${err.message}`);
    }
  };

  const toSignature = (body) => String(body).replace(/\s+/g, "").toLowerCase();
  const extractActions = (text) => {
    const list = [];
    ACTION_TAG_REGEX.lastIndex = 0;
    const counts = new Map();
    const sample = new Map();
    let m;
    while ((m = ACTION_TAG_REGEX.exec(text)) !== null) {
      const body = (m[1] || "").trim();
      if (!body || body.includes('"..."')) continue;
      const sign = toSignature(body);
      counts.set(sign, (counts.get(sign) || 0) + 1);
      if (!sample.has(sign)) sample.set(sign, body);
    }
    if (!actionBaselineReady) {
      counts.forEach((v, k) => processedActionCounts.set(k, v));
      actionBaselineReady = true;
      return [];
    }
    counts.forEach((v, k) => {
      const done = processedActionCounts.get(k) || 0;
      for (let i = 0; i < v - done; i += 1) list.push({ signature: k, body: sample.get(k), full: `<action>${sample.get(k)}</action>` });
    });
    return list;
  };

  const renderActionPanel = () => {
    if (!pendingActions.length) return actionPanel?.remove();
    if (!actionPanel) {
      actionPanel = document.createElement("div");
      actionPanel.className = "ta-action-panel";
      document.body.appendChild(actionPanel);
    }
    const listHtml = pendingActions.map((x) => `<li><code>${x.body}</code></li>`).join("");
    actionPanel.innerHTML = `
      <h4>检测到可执行动作（${pendingActions.length}）</h4>
      <ol class="ta-action-list">${listHtml}</ol>
      <div class="ta-setting-row">同步状态：<span id="ta-sync-status">${lastSyncStatus}</span></div>
      <div class="ta-actions"><button class="ta-primary" data-action="execute">执行并同步</button><button data-action="clear">忽略</button></div>`;

    actionPanel.querySelectorAll("button").forEach((btn) => btn.addEventListener("click", async () => {
      const act = btn.getAttribute("data-action");
      if (act === "clear") {
        pendingActions.forEach((x) => processedActionCounts.set(x.signature, (processedActionCounts.get(x.signature) || 0) + 1));
        pendingActions.length = 0;
        return renderActionPanel();
      }
      if (act === "execute") await executePendingActions();
    }));
  };

  const executePendingActions = async () => {
    if (actionExecuting || !pendingActions.length) return;
    actionExecuting = true;
    try {
      const model_output = pendingActions.map((x) => x.full).join("\n");
      const data = await bridgePost("/actions/execute", { model_output });
      pendingActions.forEach((x) => processedActionCounts.set(x.signature, (processedActionCounts.get(x.signature) || 0) + 1));
      pendingActions.length = 0;
      renderActionPanel();
      const eventId = data?.state_event?.event_id || "";
      if (runtimeSettings.appendResultToInput && activeEditable && isLikelyChatComposer(activeEditable)) {
        const lines = ["[Trade Assistant Action Results]"];
        (data?.results || []).forEach((r, i) => lines.push(`${i + 1}. ${r.status}: ${r.message}`));
        if (eventId) lines.push(`Event ID: ${eventId}`);
        setValue(activeEditable, `${getValue(activeEditable)}\n\n${lines.join("\n")}`.trim());
      } else {
        window.alert(`动作已同步到 APP${eventId ? `\n事件ID: ${eventId}` : ""}`);
      }
      if (runtimeSettings.openDashboardAfterExecute) window.open("http://127.0.0.1:8787/", "_blank");
    } catch (err) {
      window.alert(`动作执行失败：${err.message}`);
    } finally {
      actionExecuting = false;
    }
  };

  const hashText = (text) => {
    let h = 0;
    for (let i = 0; i < text.length; i += 1) {
      h = ((h << 5) - h) + text.charCodeAt(i);
      h |= 0;
    }
    return String(h);
  };

  const latestReplySnapshot = () => {
    const candidates = [];
    ["main", "[role='main']", "article", ".message", ".assistant"].forEach((sel) => {
      document.querySelectorAll(sel).forEach((el) => {
        const txt = (el.innerText || "").trim();
        if (txt.length > 40) candidates.push(txt);
      });
    });
    const base = candidates.length ? candidates[candidates.length - 1] : (document.body?.innerText || "");
    return String(base)
      .replace(/\[LOCAL_CONTEXT_BEGIN\][\s\S]*?\[LOCAL_CONTEXT_END\]/g, "")
      .replace(ACTION_TAG_REGEX, "")
      .trim()
      .slice(-1800);
  };

  const syncConversationToApp = async () => {
    if (!runtimeSettings.autoSyncConversation) return;
    const now = Date.now();
    if (now - lastSyncedAt < 5000) return;
    const snapshot = latestReplySnapshot();
    if (!snapshot || snapshot.length < 40) return;
    const hash = hashText(snapshot);
    if (hash === lastSyncedHash) return;
    try {
      await bridgePost("/conversation/sync", { model_name: modelName(), assistant_reply: snapshot });
      lastSyncedHash = hash;
      lastSyncedAt = now;
      lastSyncStatus = `已同步 ${new Date().toLocaleTimeString()}`;
    } catch (_err) {
      lastSyncStatus = "同步失败（将自动重试）";
    }
    if (actionPanel) {
      const statusEl = actionPanel.querySelector("#ta-sync-status");
      if (statusEl) statusEl.textContent = lastSyncStatus;
    }
  };

  const scheduleActionScan = () => {
    if (actionScanTimer) return;
    actionScanTimer = setTimeout(() => {
      actionScanTimer = null;
      const items = extractActions(document.body?.innerText || "");
      if (items.length) {
        pendingActions.length = 0;
        pendingActions.push(items[items.length - 1]);
        renderActionPanel();
      }
    }, 700);
  };

  const scheduleConversationSync = () => {
    if (conversationSyncTimer) return;
    conversationSyncTimer = setTimeout(() => {
      conversationSyncTimer = null;
      syncConversationToApp();
    }, 2500);
  };

  const ensureLauncher = () => {
    if (launcherWrap) return;
    launcherWrap = document.createElement("div");
    launcherWrap.className = "ta-launcher-wrap";
    launcherWrap.innerHTML = `
      <button type="button" class="ta-launcher-btn" title="Alt + C">@胶囊</button>
      <button type="button" class="ta-launcher-mini" title="隐藏">×</button>
    `;
    launcherBtn = launcherWrap.querySelector(".ta-launcher-btn");
    const hideBtn = launcherWrap.querySelector(".ta-launcher-mini");

    const savedPos = runtimeSettings.launcherPos;
    if (savedPos && Number.isFinite(savedPos.left) && Number.isFinite(savedPos.top)) {
      launcherWrap.style.left = `${Math.max(8, savedPos.left)}px`;
      launcherWrap.style.top = `${Math.max(8, savedPos.top)}px`;
      launcherWrap.style.bottom = "auto";
    }

    launcherBtn?.addEventListener("click", async () => {
      if (!activeEditable || !isLikelyChatComposer(activeEditable)) activeEditable = findAnyEditable();
      if (!activeEditable) return window.alert("未找到聊天输入框，请先点击对话输入区域。");
      await buildAndPreviewCapsule();
    });

    hideBtn?.addEventListener("click", async (e) => {
      e.stopPropagation();
      launcherWrap.style.display = "none";
      await saveSettings({ launcherHidden: true });
      if (!launcherRestoreBtn) {
        launcherRestoreBtn = document.createElement("button");
        launcherRestoreBtn.type = "button";
        launcherRestoreBtn.className = "ta-launcher-restore";
        launcherRestoreBtn.textContent = "@";
        launcherRestoreBtn.title = "显示胶囊入口";
        launcherRestoreBtn.addEventListener("click", async () => {
          launcherWrap.style.display = "";
          launcherRestoreBtn.remove();
          launcherRestoreBtn = null;
          await saveSettings({ launcherHidden: false });
        });
      }
      document.body.appendChild(launcherRestoreBtn);
    });

    let dragging = false;
    let offsetX = 0;
    let offsetY = 0;
    launcherWrap.addEventListener("pointerdown", (e) => {
      if (!(e.target instanceof Element) || e.target.classList.contains("ta-launcher-mini")) return;
      dragging = true;
      const rect = launcherWrap.getBoundingClientRect();
      offsetX = e.clientX - rect.left;
      offsetY = e.clientY - rect.top;
      launcherWrap.setPointerCapture?.(e.pointerId);
    });
    launcherWrap.addEventListener("pointermove", (e) => {
      if (!dragging) return;
      const left = Math.max(8, Math.min(window.innerWidth - 120, e.clientX - offsetX));
      const top = Math.max(8, Math.min(window.innerHeight - 48, e.clientY - offsetY));
      launcherWrap.style.left = `${left}px`;
      launcherWrap.style.top = `${top}px`;
      launcherWrap.style.bottom = "auto";
    });
    launcherWrap.addEventListener("pointerup", async () => {
      if (!dragging) return;
      dragging = false;
      const rect = launcherWrap.getBoundingClientRect();
      await saveSettings({ launcherPos: { left: Math.round(rect.left), top: Math.round(rect.top) } });
    });

    document.body.appendChild(launcherWrap);
    if (runtimeSettings.launcherHidden) hideBtn?.click();
  };

  const maybeShowOnboarding = () => {
    chrome.storage.local.get([ONBOARDING_KEY], (res) => {
      if (res?.[ONBOARDING_KEY]) return;
      const toast = document.createElement("div");
      toast.className = "ta-onboarding-toast";
      toast.innerHTML = `<span>提示：输入 @，或点击胶囊按钮；快捷键 Alt + C。</span><button>知道了</button>`;
      toast.querySelector("button")?.addEventListener("click", () => {
        toast.remove();
        chrome.storage.local.set({ [ONBOARDING_KEY]: true });
      });
      document.body.appendChild(toast);
    });
  };

  new MutationObserver(() => {
    scheduleActionScan();
    scheduleConversationSync();
  }).observe(document.documentElement, { childList: true, subtree: true, characterData: true });

  document.addEventListener("focusin", (e) => {
    const el = getEditable(e.target);
    if (el) activeEditable = el;
  });

  document.addEventListener("keydown", (e) => {
    const el = getEditable(e.target);
    if (el) activeEditable = el;
    if (!activeEditable || !isLikelyChatComposer(activeEditable)) return;
    if (e.key === "@" || (e.shiftKey && e.code === "Digit2")) return setTimeout(showHintChip, 0);
    if (e.altKey && (e.key === "c" || e.key === "C")) {
      e.preventDefault();
      buildAndPreviewCapsule();
    }
    if (e.key === "Escape") clearHintChip();
  });

  document.addEventListener("input", (e) => {
    const el = getEditable(e.target);
    if (!el) return;
    activeEditable = el;
    if (getValue(el).includes("@")) setTimeout(showHintChip, 0);
  });

  loadSettings().then(() => {
    ensureLauncher();
    maybeShowOnboarding();
    scheduleActionScan();
    scheduleConversationSync();
  });
})();
