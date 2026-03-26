const I18N = {
  zh: {
    brand_name: "外贸助理 Trade Assistant",
    brand_tagline: "让 AI 继承你的外贸工作习惯",
    brand_short: "TRADE_ASSISTANT",
    nav_home: "首页",
    nav_download: "下载",
    nav_docs: "文档",
    nav_privacy: "隐私",
    release_label: "当前版本",

    home_kicker: "本地优先的外贸 AI 助手",
    home_big_title: "TRADE ASSISTANT",
    home_title: "同样的问题，越用越懂你；换模型，也不用重头再来",
    home_subtitle: "导入历史邮件、报价、事件后，外贸助理会基于你的编辑反馈持续学习，形成可追溯、可迁移的个人业务记忆。",
    home_cta_download: "立即下载内测版",
    home_cta_docs: "查看新手指南",
    home_footer_note: "数据不搬家 · 能力不绑平台",

    feature_section_1_title: "核心问题",
    feature_section_1_desc: "用户觉得 AI 不聪明，本质是没有用户习惯与上下文；换模型后又要从零开始。",
    feature_section_2_title: "解决方式",
    feature_section_2_headline: "规则 + RAG + 编辑反馈成长",
    feature_section_2_desc: "先做可追溯、可解释、低错误率，再逐步增强模型能力，优先验证商业付费意愿。",
    feature_section_3_title: "核心能力",

    feature_1_title: "自动成长",
    feature_1_desc: "基于 before/after 编辑差异，自动学习你的价格偏好与话术习惯。",
    feature_2_title: "模型可切换",
    feature_2_desc: "支持 NVIDIA、OpenAI、OpenRouter、DeepSeek、千问、豆包、Google 等接口。",
    feature_3_title: "证据可追溯",
    feature_3_desc: "每次建议都可回看依据来源，降低“看着聪明但不可控”的风险。",

    home_flow_title: "使用流程",
    home_flow_1_title: "导入历史资料",
    home_flow_1_desc: "支持历史邮件、报价、事件，快速形成初始上下文。",
    home_flow_2_title: "生成并修改",
    home_flow_2_desc: "由模型先出草稿，你做最后确认和微调，保证可控。",
    home_flow_3_title: "自动成长",
    home_flow_3_desc: "系统把你的修改转成偏好权重，下次自动命中更高。",

    agent_ready_title: "Agent Ready",
    agent_ready_desc: "网站预留机器可读入口，便于未来 Agent-to-Agent 对接。",

    download_kicker: "发布渠道",
    download_title: "内测版本下载",
    download_subtitle: "优先读取站内发布清单，失败时回退到 GitHub Release。",
    download_card_win_title: "Windows",
    download_card_mac_title: "macOS",
    download_button_win: "下载 Windows 包",
    download_button_mac: "下载 macOS 包",
    download_notice_title: "安装提示",
    download_notice_1: "先看新手文档，再开始安装。",
    download_notice_2: "macOS 首次可能出现“未验证开发者”，按文档流程放行。",
    download_notice_3: "建议保留上一个稳定包，出现问题可快速回滚。",
    download_fallback_note: "如果下载按钮显示 unavailable，表示发布资产还在同步。",

    docs_kicker: "快速上手",
    docs_title: "新手安装与使用",
    docs_intro: "先安装，再配置 API，最后导入历史资料并开始让 AI 学习你的习惯。",
    docs_quickstart_title: "新手三步",
    docs_quickstart_1: "下载并解压对应系统的内测包（Windows 或 macOS）。",
    docs_quickstart_2: "启动桌面助手，在 API Settings 填入你的模型 API 信息。",
    docs_quickstart_3: "点击一键启动，导入历史资料和邮件线程开始使用。",
    docs_windows_title: "Windows 安装",
    docs_windows_1: "先解压到本地目录，不要在压缩包内直接运行。",
    docs_windows_2: "双击 Launch_InVault_Windows.bat。",
    docs_windows_3: "若出现安全提示，选择“更多信息 -> 仍要运行”。",
    docs_mac_title: "macOS 安装",
    docs_mac_1: "首次被拦截时，打开“系统设置 -> 隐私与安全性”。",
    docs_mac_2: "在底部找到应用拦截提示，点击“仍要打开”。",
    docs_mac_3: "若仍提示损坏，在终端执行：xattr -dr com.apple.quarantine /Applications/InVault.app。",

    privacy_kicker: "隐私宪章",
    privacy_title: "隐私与数据主权",
    privacy_intro: "外贸助理采用本地优先策略：业务资料、偏好和成长记录默认保留在你的设备中。",
    privacy_principles_title: "核心原则",
    privacy_1: "默认不上传原始历史资料到云端存储。",
    privacy_2: "敏感配置可在本地系统能力下加密保存。",
    privacy_3: "你可以导出并迁移自己的数据，不被单一平台绑定。",
    privacy_4: "若调用第三方模型 API，请遵守对应厂商的数据政策。"
  },
  en: {
    brand_name: "Trade Assistant",
    brand_tagline: "Let AI inherit your trade workflow habits",
    brand_short: "TRADE_ASSISTANT",
    nav_home: "Home",
    nav_download: "Download",
    nav_docs: "Docs",
    nav_privacy: "Privacy",
    release_label: "Version",

    home_kicker: "Local-First AI Trade Copilot",
    home_big_title: "TRADE ASSISTANT",
    home_title: "Same request, smarter over time. Switch models without restarting memory.",
    home_subtitle: "Import your historical emails, quotes and events. Trade Assistant learns from your edits and builds traceable, portable memory.",
    home_cta_download: "Download Beta",
    home_cta_docs: "Quick Start",
    home_footer_note: "Data stays with you · Capability stays portable",

    feature_section_1_title: "Core Problem",
    feature_section_1_desc: "AI feels generic because it lacks user-specific habits and context; model switching resets everything.",
    feature_section_2_title: "Approach",
    feature_section_2_headline: "Rules + RAG + Edit-Feedback Growth",
    feature_section_2_desc: "Prioritize traceability, explainability, and low error rate first; scale model sophistication after validation.",
    feature_section_3_title: "Core Capabilities",

    feature_1_title: "Adaptive Learning",
    feature_1_desc: "Learns pricing and tone preferences from before/after edits.",
    feature_2_title: "Model Switch Ready",
    feature_2_desc: "Supports NVIDIA, OpenAI, OpenRouter, DeepSeek, Qwen, Doubao, Google and custom endpoints.",
    feature_3_title: "Traceable Evidence",
    feature_3_desc: "Each suggestion can be traced back to source snippets and rules.",

    home_flow_title: "Workflow",
    home_flow_1_title: "Import History",
    home_flow_1_desc: "Import emails, quotes, and events to establish high-quality context.",
    home_flow_2_title: "Generate & Edit",
    home_flow_2_desc: "Model drafts first, you finalize with controlled edits.",
    home_flow_3_title: "Auto Growth",
    home_flow_3_desc: "Your edits are converted into preference weights for better next responses.",

    agent_ready_title: "Agent Ready",
    agent_ready_desc: "Machine-readable endpoints are reserved for future Agent-to-Agent integration.",

    download_kicker: "Release Channel",
    download_title: "Beta Downloads",
    download_subtitle: "Read local release manifest first, then fallback to GitHub Release.",
    download_card_win_title: "Windows",
    download_card_mac_title: "macOS",
    download_button_win: "Download for Windows",
    download_button_mac: "Download for macOS",
    download_notice_title: "Install Notes",
    download_notice_1: "Read quick-start docs before installation.",
    download_notice_2: "On first launch macOS may block unknown developer apps. Follow docs to allow.",
    download_notice_3: "Keep the last stable package so you can rollback quickly.",
    download_fallback_note: "If a download button shows unavailable, release assets are still syncing.",

    docs_kicker: "Quick Start Manual",
    docs_title: "Install & First Use",
    docs_intro: "Install first, configure API second, then import your history to start adaptive learning.",
    docs_quickstart_title: "3-Step Onboarding",
    docs_quickstart_1: "Download and unzip the beta package for your OS (Windows or macOS).",
    docs_quickstart_2: "Launch desktop assistant and fill in API settings.",
    docs_quickstart_3: "Click one-click start, then import your history and email threads.",
    docs_windows_title: "Windows Install",
    docs_windows_1: "Unzip first. Do not run directly inside the zip file.",
    docs_windows_2: "Double click Launch_InVault_Windows.bat.",
    docs_windows_3: "If SmartScreen appears, click More info -> Run anyway.",
    docs_mac_title: "macOS Install",
    docs_mac_1: "If blocked at first launch, open System Settings -> Privacy & Security.",
    docs_mac_2: "Find the blocked app section and click Open Anyway.",
    docs_mac_3: "If still blocked as damaged, run: xattr -dr com.apple.quarantine /Applications/InVault.app",

    privacy_kicker: "Privacy Charter",
    privacy_title: "Privacy & Data Sovereignty",
    privacy_intro: "Trade Assistant is local-first: your business data, preferences, and growth logs stay on your device by default.",
    privacy_principles_title: "Core Principles",
    privacy_1: "Raw history is not uploaded to cloud storage by default.",
    privacy_2: "Sensitive settings can be stored with local OS-backed encryption.",
    privacy_3: "You can export and migrate your data at any time.",
    privacy_4: "If you use third-party model APIs, follow each provider's data policy."
  }
};

function byId(id) {
  return document.getElementById(id);
}

function applyLang(lang) {
  const dict = I18N[lang] || I18N.zh;
  document.documentElement.lang = lang === "zh" ? "zh-CN" : "en";
  localStorage.setItem("ta_lang", lang);

  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    if (dict[key]) {
      el.textContent = dict[key];
    }
  });

  const toggle = byId("lang-toggle");
  if (toggle) {
    toggle.textContent = lang === "zh" ? "EN" : "中文";
  }
}

function setFooterYear() {
  const y = byId("year");
  if (y) y.textContent = String(new Date().getFullYear());
}

function setAssetLink(anchorId, nameId, asset, fallbackText) {
  const a = byId(anchorId);
  const n = byId(nameId);
  if (!a || !n) return;
  if (!asset || !asset.url) {
    n.textContent = fallbackText;
    a.classList.add("disabled");
    a.setAttribute("aria-disabled", "true");
    a.href = "#";
    return;
  }
  n.textContent = asset.name;
  a.classList.remove("disabled");
  a.removeAttribute("aria-disabled");
  a.href = asset.url;
}

function pickAssets(assets) {
  const list = Array.isArray(assets) ? assets : [];
  const win = list.find((a) => /win(dows)?|\.exe|_windows\.zip/i.test(a.name || ""));
  const mac = list.find((a) => /mac|\.dmg|_mac\.zip/i.test(a.name || ""));
  return { win, mac };
}

async function fetchManifest() {
  const localRes = await fetch("./api/release-manifest.json", { cache: "no-store" });
  if (!localRes.ok) {
    throw new Error(`manifest status ${localRes.status}`);
  }
  return await localRes.json();
}

async function fetchGithubFallback() {
  const repo = "tongxigogo-crypto/foreign-trade-assistant";
  const res = await fetch(`https://api.github.com/repos/${repo}/releases/latest`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`github status ${res.status}`);
  }
  const data = await res.json();
  return {
    version: data.tag_name || "unknown",
    published_at: data.published_at || null,
    assets: (data.assets || []).map((a) => ({ name: a.name, url: a.browser_download_url }))
  };
}

async function initDownloadPage() {
  if (document.body.dataset.page !== "download") return;
  const versionNode = byId("version-tag");

  let manifest;
  try {
    manifest = await fetchManifest();
  } catch {
    try {
      manifest = await fetchGithubFallback();
    } catch {
      manifest = {
        version: "unavailable",
        assets: []
      };
    }
  }

  if (versionNode) versionNode.textContent = manifest.version || "unknown";
  const assets = pickAssets(manifest.assets || []);
  setAssetLink("win-download", "win-asset-name", assets.win, "not available");
  setAssetLink("mac-download", "mac-asset-name", assets.mac, "not available");
}

function init() {
  const lang = localStorage.getItem("ta_lang") || "zh";
  applyLang(lang);
  setFooterYear();

  const toggle = byId("lang-toggle");
  if (toggle) {
    toggle.addEventListener("click", () => {
      const next = (localStorage.getItem("ta_lang") || "zh") === "zh" ? "en" : "zh";
      applyLang(next);
    });
  }

  initDownloadPage();
}

init();
