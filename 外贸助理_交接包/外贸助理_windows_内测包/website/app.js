const I18N = {
  zh: {
    brand_name: "Tongxi Dev Site",
    brand_tagline: "个人开发与产品实验",
    brand_short: "TONGXI_DEV",
    nav_home: "首页",
    nav_download: "外贸助理下载",
    nav_docs: "外贸助理文档",
    nav_privacy: "外贸助理隐私",
    release_label: "当前版本",

    home_kicker: "PERSONAL DEV PORTFOLIO",
    home_big_title: "TONGXI LAB",
    home_title: "个人开发网站",
    home_subtitle: "这是我的个人开发网站，用于展示我持续迭代的应用与自动化产品。外贸助理是当前主推项目，后续会陆续上架更多作品。",
    home_cta_download: "体验外贸助理",
    home_cta_docs: "查看项目文档",
    home_footer_note: "持续构建 · 持续交付 · 持续进化",

    hero_right_kicker: "Current Focus",
    hero_right_title: "外贸助理（Trade Assistant）",
    hero_right_desc: "当前主线是可追溯、可解释、低错误率的 AI 决策层，目标是服务真实业务并形成可验证的产品闭环。",
    hero_right_point_1: "• 本地优先：业务数据默认在用户设备",
    hero_right_point_2: "• 自动成长：基于编辑反馈持续优化",
    hero_right_point_3: "• 模型可切换：减少平台绑定",

    feature_section_1_title: "网站定位",
    feature_section_1_desc: "一个可持续更新的个人产品站：展示能力、沉淀案例、连接用户反馈，并持续发布新版本。",
    feature_section_2_title: "当前主线",
    feature_section_2_headline: "外贸助理 Trade Assistant",
    feature_section_2_desc: "聚焦“自动成长 + 可追溯 + 跨模型复用”，服务不懂技术的一线业务用户。",
    feature_section_3_title: "已开发应用",

    feature_1_title: "外贸助理",
    feature_1_desc: "本地优先的外贸 AI 参谋，支持历史导入、动作注入、偏好成长和多模型 API。",
    feature_2_title: "Video Workflow Test Beta",
    feature_2_desc: "面向视频生产流程的自动化实验项目，用于验证多步骤智能工作流。",
    feature_3_title: "MiniProgram Recovered",
    feature_3_desc: "小程序项目恢复与工程化重构实践，保留业务结构并重建可维护开发链路。",

    home_flow_title: "下一批上架计划",
    home_flow_1_title: "Agent 协作工具",
    home_flow_1_desc: "面向多模型协同工作的轻量调度与日志管理工具。",
    home_flow_2_title: "自动化运营面板",
    home_flow_2_desc: "统一查看反馈、版本、指标和发布状态，提升个人开发效率。",
    home_flow_3_title: "跨端发布工具链",
    home_flow_3_desc: "继续强化 Windows / macOS 双端打包与更新体验。",

    agent_ready_title: "Agent Ready",
    agent_ready_desc: "Machine-readable endpoints are reserved for future Agent-to-Agent integration.",

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
    brand_name: "Tongxi Dev Site",
    brand_tagline: "Personal products and dev experiments",
    brand_short: "TONGXI_DEV",
    nav_home: "Home",
    nav_download: "TA Download",
    nav_docs: "TA Docs",
    nav_privacy: "TA Privacy",
    release_label: "Version",

    home_kicker: "PERSONAL DEV PORTFOLIO",
    home_big_title: "TONGXI LAB",
    home_title: "Personal Dev Website",
    home_subtitle: "This is my personal development website for showcasing continuously evolving apps and automation products. Trade Assistant is the current focus, with more projects to be added.",
    home_cta_download: "Try Trade Assistant",
    home_cta_docs: "View Project Docs",
    home_footer_note: "Build Fast · Ship Often · Improve Continuously",

    hero_right_kicker: "Current Focus",
    hero_right_title: "Trade Assistant",
    hero_right_desc: "Current track is a traceable, explainable, low-error AI decision layer for real business workflows.",
    hero_right_point_1: "• Local-first: business data stays on user device by default",
    hero_right_point_2: "• Adaptive growth: continuously improves from edit feedback",
    hero_right_point_3: "• Multi-model ready: reduces platform lock-in",

    feature_section_1_title: "Site Positioning",
    feature_section_1_desc: "A continuously updated personal product site: show capabilities, accumulate cases, collect feedback, and ship new versions.",
    feature_section_2_title: "Current Mainline",
    feature_section_2_headline: "Trade Assistant",
    feature_section_2_desc: "Focused on adaptive growth, traceability, and model portability for non-technical frontline users.",
    feature_section_3_title: "Built Applications",

    feature_1_title: "Trade Assistant",
    feature_1_desc: "Local-first AI copilot for trade operations with history import, action injection, preference growth, and multi-model APIs.",
    feature_2_title: "Video Workflow Test Beta",
    feature_2_desc: "An automation experiment for video production workflows, validating multi-step intelligent orchestration.",
    feature_3_title: "MiniProgram Recovered",
    feature_3_desc: "Mini-program recovery and engineering refactor to restore business structure and maintainable workflows.",

    home_flow_title: "Next Releases",
    home_flow_1_title: "Agent Collaboration Toolkit",
    home_flow_1_desc: "Lightweight scheduling and logging tools for multi-model collaborative work.",
    home_flow_2_title: "Automation Ops Panel",
    home_flow_2_desc: "Unified panel for feedback, versions, metrics, and release status.",
    home_flow_3_title: "Cross-Platform Release Toolchain",
    home_flow_3_desc: "Further improve Windows/macOS packaging and update experience.",

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

function byId(id) { return document.getElementById(id); }

function applyLang(lang) {
  const dict = I18N[lang] || I18N.zh;
  document.documentElement.lang = lang === "zh" ? "zh-CN" : "en";
  localStorage.setItem("ta_lang", lang);

  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    if (dict[key]) el.textContent = dict[key];
  });

  const toggle = byId("lang-toggle");
  if (toggle) toggle.textContent = lang === "zh" ? "EN" : "中文";
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
  if (!localRes.ok) throw new Error(`manifest status ${localRes.status}`);
  return await localRes.json();
}

async function fetchGithubFallback() {
  const repo = "tongxigogo-crypto/foreign-trade-assistant";
  const res = await fetch(`https://api.github.com/repos/${repo}/releases/latest`, { cache: "no-store" });
  if (!res.ok) throw new Error(`github status ${res.status}`);
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
      manifest = { version: "unavailable", assets: [] };
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
