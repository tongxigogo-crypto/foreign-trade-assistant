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
  };

  let activeEditable = null;
  let hintChip = null;
  let actionPanel = null;
  let launcherBtn = null;
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

  const getEditable = (node) => {
    if (!node) return null;
    const start = node.nodeType === Node.TEXT_NODE ? node.parentElement : node;
    if (!start) return null;
    if (isEditable(start)) return start;
    return start.closest?.('textarea,input,[contenteditable="true"],[contenteditable=""],[contenteditable]') || null;
  };

  const findAnyEditable = () =>
    document.querySelector('textarea,input[type="text"],input[type="search"],[contenteditable="true"],[contenteditable=""],[contenteditable]');

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
        if (btn.getAttribute("data-action") === "confirm") setValue(activeEditable, capsule.injected_prompt || getValue(activeEditable));
        mask.remove();
      });
    });
    document.body.appendChild(mask);
  };

  const buildAndPreviewCapsule = async () => {
    if (!activeEditable) return;
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
      <div class="ta-setting-row"><label><input id="ta-setting-auto-sync" type="checkbox" ${runtimeSettings.autoSyncConversation ? "checked" : ""}/> 自动同步大模型回复到 APP 记忆</label></div>
      <div class="ta-setting-row">
        <label>注入模板语言：
          <select id="ta-setting-template-lang">
            <option value="zh" ${runtimeSettings.templateLang === "zh" ? "selected" : ""}>中文</option>
            <option value="en" ${runtimeSettings.templateLang === "en" ? "selected" : ""}>English</option>
          </select>
        </label>
      </div>
      <div class="ta-setting-row">
        <label>注入模板模式：
          <select id="ta-setting-template-mode">
            <option value="standard" ${runtimeSettings.templateMode === "standard" ? "selected" : ""}>标准</option>
            <option value="compact" ${runtimeSettings.templateMode === "compact" ? "selected" : ""}>简洁</option>
            <option value="custom" ${runtimeSettings.templateMode === "custom" ? "selected" : ""}>自定义</option>
          </select>
        </label>
      </div>
      <div class="ta-setting-row" id="ta-custom-instruction-wrap" style="${runtimeSettings.templateMode === "custom" ? "" : "display:none;"}">
        <label>自定义指令：</label>
        <textarea id="ta-setting-custom-instruction" rows="3" style="width:100%;">${(runtimeSettings.customInstruction || "").replaceAll("<", "&lt;")}</textarea>
      </div>
      <div class="ta-setting-row">同步状态：<span id="ta-sync-status">${lastSyncStatus}</span></div>
      <details class="ta-setting-row">
        <summary>高级设置</summary>
        <label><input id="ta-setting-append" type="checkbox" ${runtimeSettings.appendResultToInput ? "checked" : ""}/> 执行结果回填输入框</label><br/>
        <label><input id="ta-setting-open-dashboard" type="checkbox" ${runtimeSettings.openDashboardAfterExecute ? "checked" : ""}/> 执行后打开 APP 网页看板</label>
      </details>
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

    actionPanel.querySelector("#ta-setting-append")?.addEventListener("change", async (e) => saveSettings({ appendResultToInput: Boolean(e.target.checked) }));
    actionPanel.querySelector("#ta-setting-open-dashboard")?.addEventListener("change", async (e) => saveSettings({ openDashboardAfterExecute: Boolean(e.target.checked) }));
    actionPanel.querySelector("#ta-setting-auto-sync")?.addEventListener("change", async (e) => saveSettings({ autoSyncConversation: Boolean(e.target.checked) }));
    actionPanel.querySelector("#ta-setting-template-lang")?.addEventListener("change", async (e) => saveSettings({ templateLang: String(e.target.value || "zh") }));
    actionPanel.querySelector("#ta-setting-template-mode")?.addEventListener("change", async (e) => {
      const mode = String(e.target.value || "standard");
      await saveSettings({ templateMode: mode });
      renderActionPanel();
    });
    actionPanel.querySelector("#ta-setting-custom-instruction")?.addEventListener("change", async (e) => {
      await saveSettings({ customInstruction: String(e.target.value || "").trim() });
    });
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
      if (runtimeSettings.appendResultToInput && activeEditable) {
        const lines = ["[Trade Assistant Action Results]"];
        (data?.results || []).forEach((r, i) => {
          lines.push(`${i + 1}. ${r.status}: ${r.message}`);
          (r.artifacts || []).forEach((a) => lines.push(`- artifact: ${a}`));
        });
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
    if (launcherBtn) return;
    launcherBtn = document.createElement("button");
    launcherBtn.type = "button";
    launcherBtn.className = "ta-launcher-btn";
    launcherBtn.textContent = "@胶囊";
    launcherBtn.title = "打开本地胶囊（Alt + C）";
    launcherBtn.addEventListener("click", async () => {
      if (!activeEditable || !isEditable(activeEditable)) activeEditable = findAnyEditable();
      if (!activeEditable) return window.alert("未找到可输入区域，请先点击输入框。");
      await buildAndPreviewCapsule();
    });
    document.body.appendChild(launcherBtn);
  };

  const maybeShowOnboarding = () => {
    chrome.storage.local.get([ONBOARDING_KEY], (res) => {
      if (res?.[ONBOARDING_KEY]) return;
      const toast = document.createElement("div");
      toast.className = "ta-onboarding-toast";
      toast.innerHTML = `<span>提示：输入 @，或点击左下角“@胶囊”；快捷键 Alt + C。</span><button>知道了</button>`;
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
    if (!activeEditable || !isEditable(activeEditable)) return;
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
