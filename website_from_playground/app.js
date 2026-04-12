import { measureLineStats, measureNaturalWidth, prepareWithSegments } from "./vendor/pretext/layout.js";

const I18N = {
  zh: {
    brand_name: "Tongxi Fairy Lab",
    brand_tagline: "宠物 IP · 工具产品 · 国际贸易准备",
    nav_home: "首页",
    nav_pet_ip: "宠物 IP",
    nav_download: "外贸助理",
    nav_pet_trade: "国际贸易",
    nav_mini_program: "小程序开发",
    nav_contact: "联系我",
    footer_note: "更轻的首页，更长的业务准备周期。",
    home_kicker: "Personal Site Rebuild",
    hero_title: "Tongxi Fairy Lab",
    hero_intro: "这是一个围绕宠物 IP、外贸助理、宠物用品国际贸易与小程序开发展开的个人网站，用更轻的结构表达更长的业务路线。",
    hero_bridge: "宠物 IP 提供品牌记忆，外贸助理提供实际能力，它们共同为后续宠物用品国际贸易做准备。",
    hero_cta_primary: "查看外贸助理",
    hero_cta_secondary: "了解宠物 IP",
    hero_summary_title: "四个入口，一条更清晰的业务主线",
    hero_summary_body: "首页不再把所有内容堆成一个重场景，而是用左右交叉的节奏，让用户快速看懂“品牌、工具、贸易、开发”之间的关系。",
    hero_chip_1: "轻童话气质",
    hero_chip_2: "Apple 式秩序",
    hero_chip_3: "快速加载",
    pet_ip_label: "01 · Pet IP",
    pet_ip_title: "宠物 IP 是整个网站的情感入口",
    pet_ip_body: "它负责建立温度、审美和记忆点，让站点不只是工具展示，而是一个有长期品牌潜力的个人项目体系。",
    pet_ip_point_1: "保持温暖、童话感的视觉记忆，但不过度幼态。",
    pet_ip_point_2: "为后续宠物用品国际贸易提供自然的品牌起点。",
    pet_ip_point_3: "为内容、产品包装和小程序体验提供统一形象。",
    pet_ip_link: "继续浏览首页叙事",
    trade_assistant_label: "02 · Trade Assistant",
    trade_assistant_title: "外贸助理把品牌想法变成实际业务能力",
    trade_assistant_body: "它不是孤立的软件下载页，而是整个个人网站里最务实的一环：帮助我验证真实业务流程，积累效率工具和后续贸易能力。",
    trade_assistant_point_1: "本地优先、可持续成长、多模型兼容。",
    trade_assistant_point_2: "为未来宠物用品国际贸易提供运营与客户处理基础。",
    trade_assistant_point_3: "也是网站当前最直接的产品转化入口。",
    trade_assistant_link: "查看下载入口",
    pet_trade_label: "03 · Pet Trade",
    pet_trade_title: "宠物用品国际贸易是后续真正要落地的方向",
    pet_trade_body: "这个入口解释为什么首页同时出现宠物 IP 和外贸助理。前者提供产品想象力与品牌感，后者提供效率与流程能力，最终都汇聚到宠物用品国际贸易。",
    pet_trade_point_1: "围绕品牌、产品表达、跨境场景和交付能力形成闭环。",
    pet_trade_point_2: "先做好内容与工具，再逐步推进商品与渠道。",
    pet_trade_point_3: "这是连接个人网站与未来业务的主线页面。",
    pet_trade_link: "查看国际贸易方向",
    mini_program_label: "04 · Mini Program",
    mini_program_title: "小程序开发负责把体验和业务落到可用产品里",
    mini_program_body: "无论是品牌展示、宠物 IP 周边互动，还是贸易相关的轻量工具，小程序开发都提供了更贴近真实用户场景的产品化能力。",
    mini_program_point_1: "适合做展示、互动、轻运营和业务试验。",
    mini_program_point_2: "能把宠物品牌内容与工具能力连接到更轻的入口。",
    mini_program_point_3: "是网站未来服务化和产品化的重要支撑。",
    mini_program_link: "查看小程序开发",
    contact_label: "05 · Contact",
    contact_title: "如果你想聊合作、产品或后续上线，直接联系我",
    contact_body: "这里保留为最终上线前的联系入口。当前先把结构固定下来，后续会补入正式邮箱、微信或表单方式。",
    contact_point_1: "适合沟通宠物 IP、产品合作和国际贸易准备。",
    contact_point_2: "也适合咨询小程序开发和定制化轻工具。",
    contact_point_3: "上线前会统一替换为正式联系方式。",
    contact_cta_primary: "联系我",
    contact_note: "正式联系方式将在上线前确认",
    download_kicker: "Trade Assistant",
    download_title: "外贸助理下载",
    download_intro: "这是当前最可直接体验的产品入口。它承担“效率工具 + 业务流程验证”的职责，也是未来宠物用品国际贸易准备阶段最重要的能力底座。",
    release_label: "当前版本",
    download_card_win_title: "Windows",
    download_card_win_headline: "桌面端内测包",
    download_card_win_desc: "适合日常业务使用与流程验证，优先读取站内发布清单，失败时回退到 GitHub Release。",
    download_button_win: "下载 Windows 包",
    download_card_mac_title: "macOS",
    download_card_mac_headline: "适合轻办公与演示",
    download_card_mac_desc: "macOS 版本面向更轻的移动办公场景，保留站点优先分发与回退机制。",
    download_button_mac: "下载 macOS 包",
    download_notice_title: "为什么它会出现在这个网站里",
    download_notice_1: "它是当前最成熟、最接近真实业务使用的一环。",
    download_notice_2: "它为未来宠物用品国际贸易提供客户处理、资料管理和工作流基础。",
    download_notice_3: "它和宠物 IP 不是并列项目，而是同一长期方向里的“工具能力层”。",
    download_fallback_note: "如果按钮显示 unavailable，表示发布资产还在同步。",
    pet_trade_page_kicker: "Pet Trade Strategy",
    pet_trade_page_title: "宠物用品国际贸易",
    pet_trade_page_intro: "这不是一个突然出现的新方向，而是整个网站从宠物 IP 到外贸助理再到小程序能力逐步汇聚出来的长期业务路径。",
    pet_trade_page_card_1_label: "品牌端",
    pet_trade_page_card_1_title: "宠物 IP 提供产品想象力",
    pet_trade_page_card_1_body: "宠物 IP 让未来的商品不只是单纯上架，而是天然拥有品牌气质、故事入口和更友好的表达方式。",
    pet_trade_page_card_2_label: "能力端",
    pet_trade_page_card_2_title: "外贸助理提供业务基础",
    pet_trade_page_card_2_body: "通过真实流程中的资料整理、客户处理和效率优化，先把“做生意的能力层”准备好，再谈商品和渠道放大。",
    pet_trade_page_note_title: "为什么这个方向适合放在个人网站里",
    pet_trade_page_note_1: "它把视觉品牌、产品工具和真实业务连接成一条清晰主线。",
    pet_trade_page_note_2: "它允许先轻量验证，再逐步进入商品、渠道和交付。",
    pet_trade_page_note_3: "它让网站既保留表达力，也保留未来商业化的可解释性。",
    mini_program_page_kicker: "Mini Program Capability",
    mini_program_page_title: "小程序开发",
    mini_program_page_intro: "小程序开发是这个网站里的执行层能力。它能把宠物 IP、贸易场景和工具能力变成更靠近真实用户的轻产品与轻运营入口。",
    mini_program_page_card_1_label: "体验端",
    mini_program_page_card_1_title: "把内容变成可互动入口",
    mini_program_page_card_1_body: "适合承接宠物 IP 展示、活动互动、轻内容分发和品牌触点，降低用户进入门槛。",
    mini_program_page_card_2_label: "业务端",
    mini_program_page_card_2_title: "把工具能力变成可用产品",
    mini_program_page_card_2_body: "适合验证小范围业务流程、客户交互和轻运营场景，是从网站展示走向实际服务的重要桥梁。",
    mini_program_page_note_title: "这个入口在整体重建里的角色",
    mini_program_page_note_1: "它证明网站不仅有审美和方向，也有落地执行能力。",
    mini_program_page_note_2: "它能连接宠物品牌表达与未来业务工具化需求。",
    mini_program_page_note_3: "它适合成为后续贸易相关轻服务和展示模块的承载层。",
  },
  en: {
    brand_name: "Tongxi Fairy Lab",
    brand_tagline: "Pet IP · Product Tools · Trade Preparation",
    nav_home: "Home",
    nav_pet_ip: "Pet IP",
    nav_download: "Trade Assistant",
    nav_pet_trade: "Pet Trade",
    nav_mini_program: "Mini Programs",
    nav_contact: "Contact",
    footer_note: "A lighter homepage for a longer business runway.",
    home_kicker: "Personal Site Rebuild",
    hero_title: "Tongxi Fairy Lab",
    hero_intro: "A personal site built around Pet IP, Trade Assistant, pet supplies international trade, and mini-program development, expressed through a lighter and faster structure.",
    hero_bridge: "The pet IP builds emotional memory, the Trade Assistant builds practical capability, and together they prepare for future pet supplies international trade.",
    hero_cta_primary: "View Trade Assistant",
    hero_cta_secondary: "Explore Pet IP",
    hero_summary_title: "Four entries, one clearer business path",
    hero_summary_body: "The homepage no longer relies on a heavy scene. It uses an alternating rhythm so users can quickly understand how brand, tool, trade, and development fit together.",
    hero_chip_1: "Fairytale softness",
    hero_chip_2: "Apple-like order",
    hero_chip_3: "Fast loading",
    pet_ip_label: "01 · Pet IP",
    pet_ip_title: "Pet IP is the emotional entry to the whole site",
    pet_ip_body: "It gives the site warmth, taste, and memorability so the work reads as a long-term brand system instead of a loose tool showcase.",
    pet_ip_point_1: "Keep a warm fairytale memory without becoming childish.",
    pet_ip_point_2: "Create a natural brand starting point for later pet supplies trade.",
    pet_ip_point_3: "Unify content, packaging, and mini-program experiences.",
    pet_ip_link: "Continue the homepage story",
    trade_assistant_label: "02 · Trade Assistant",
    trade_assistant_title: "Trade Assistant turns brand ideas into practical capability",
    trade_assistant_body: "It is not an isolated download page. It is the most practical layer in the site, helping validate real workflows while building future trade capability.",
    trade_assistant_point_1: "Local-first, adaptive, and multi-model ready.",
    trade_assistant_point_2: "Builds an operational base for future pet supplies trade.",
    trade_assistant_point_3: "It is also the clearest current conversion entry on the site.",
    trade_assistant_link: "Open the download entry",
    pet_trade_label: "03 · Pet Trade",
    pet_trade_title: "Pet supplies international trade is the real long-term direction",
    pet_trade_body: "This entry explains why Pet IP and Trade Assistant appear together. One builds product imagination and brand feeling, the other builds workflow and efficiency, and both converge into pet supplies international trade.",
    pet_trade_point_1: "Unify brand, product expression, cross-border scenarios, and delivery capability.",
    pet_trade_point_2: "Build content and tools first, then expand into goods and channels.",
    pet_trade_point_3: "This is the page that ties the site to future business.",
    pet_trade_link: "View the trade direction",
    mini_program_label: "04 · Mini Program",
    mini_program_title: "Mini-program development turns experience and business into usable products",
    mini_program_body: "Whether for brand presence, pet IP interaction, or lightweight trade tools, mini-program development creates productized entry points closer to real users.",
    mini_program_point_1: "Useful for display, interaction, light operations, and experiments.",
    mini_program_point_2: "Connects pet-brand content with lightweight product utility.",
    mini_program_point_3: "A key support layer for future services and productization.",
    mini_program_link: "View mini-program work",
    contact_label: "05 · Contact",
    contact_title: "If you want to talk about collaboration, products, or launch plans, contact me here",
    contact_body: "This section is reserved as the final contact entry before launch. The structure is fixed now, and the final email, WeChat, or form will be filled in before going live.",
    contact_point_1: "For pet IP, product collaboration, and trade preparation conversations.",
    contact_point_2: "Also suitable for mini-program development and lightweight custom tools.",
    contact_point_3: "The final contact method will be confirmed before launch.",
    contact_cta_primary: "Contact Me",
    contact_note: "Final contact details will be confirmed before launch",
    download_kicker: "Trade Assistant",
    download_title: "Trade Assistant Downloads",
    download_intro: "This is the most directly usable product entry today. It carries the role of workflow validation and operational tooling, which makes it a core capability layer for future pet supplies trade preparation.",
    release_label: "Current version",
    download_card_win_title: "Windows",
    download_card_win_headline: "Desktop beta package",
    download_card_win_desc: "Best for daily workflow validation. It reads the local release manifest first and falls back to GitHub Release when needed.",
    download_button_win: "Download for Windows",
    download_card_mac_title: "macOS",
    download_card_mac_headline: "For lighter mobile work",
    download_card_mac_desc: "The macOS build supports lighter work and demo flows while keeping the same site-first release path.",
    download_button_mac: "Download for macOS",
    download_notice_title: "Why this page belongs in the site",
    download_notice_1: "It is currently the most mature and real-world-ready product layer.",
    download_notice_2: "It builds the customer handling, knowledge organization, and workflow foundation for future pet supplies trade.",
    download_notice_3: "It is not parallel to Pet IP. It is the tooling layer inside the same long-term direction.",
    download_fallback_note: "If a button shows unavailable, release assets are still syncing.",
    pet_trade_page_kicker: "Pet Trade Strategy",
    pet_trade_page_title: "Pet Supplies International Trade",
    pet_trade_page_intro: "This is not a sudden new direction. It is the long-term business path formed by the gradual convergence of Pet IP, Trade Assistant, and mini-program capability.",
    pet_trade_page_card_1_label: "Brand side",
    pet_trade_page_card_1_title: "Pet IP creates product imagination",
    pet_trade_page_card_1_body: "Pet IP makes future goods feel branded, memorable, and story-led instead of just being listed as products.",
    pet_trade_page_card_2_label: "Capability side",
    pet_trade_page_card_2_title: "Trade Assistant builds the operating base",
    pet_trade_page_card_2_body: "By handling real workflow problems first, it prepares the capability layer required before scaling products and channels.",
    pet_trade_page_note_title: "Why this direction belongs on a personal site",
    pet_trade_page_note_1: "It links visual brand, tool products, and real business into one clear path.",
    pet_trade_page_note_2: "It allows lightweight validation before moving into goods, channels, and delivery.",
    pet_trade_page_note_3: "It keeps the site expressive while making future commercialization legible.",
    mini_program_page_kicker: "Mini Program Capability",
    mini_program_page_title: "Mini-Program Development",
    mini_program_page_intro: "Mini-program development is the execution layer on this site. It can turn the pet IP, trade scenarios, and tool capability into lightweight products and operational entry points closer to real users.",
    mini_program_page_card_1_label: "Experience side",
    mini_program_page_card_1_title: "Turn content into interactive entry points",
    mini_program_page_card_1_body: "Useful for pet IP showcases, event interaction, lightweight content distribution, and brand touchpoints.",
    mini_program_page_card_2_label: "Business side",
    mini_program_page_card_2_title: "Turn tool capability into usable products",
    mini_program_page_card_2_body: "Useful for validating small-scale workflows, customer interaction, and light operations as the site moves toward real services.",
    mini_program_page_note_title: "Its role in the rebuild",
    mini_program_page_note_1: "It proves the site has execution ability, not just aesthetics and direction.",
    mini_program_page_note_2: "It connects pet-brand expression with future business tooling needs.",
    mini_program_page_note_3: "It is a natural host for future trade-related light services and experience modules.",
  },
};

const byId = (id) => document.getElementById(id);

function applyLang(lang) {
  const dict = I18N[lang] || I18N.zh;
  document.documentElement.lang = lang === "zh" ? "zh-CN" : "en";
  localStorage.setItem("ta_lang", lang);
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    if (key && dict[key]) el.textContent = dict[key];
  });
  const toggle = byId("lang-toggle");
  if (toggle) toggle.textContent = lang === "zh" ? "EN" : "中文";
}

function setFooterYear() {
  const year = byId("year");
  if (year) year.textContent = String(new Date().getFullYear());
}

function revealSections() {
  const nodes = [...document.querySelectorAll(".fade-in")];
  if (!nodes.length || !("IntersectionObserver" in window)) {
    nodes.forEach((node) => node.classList.add("is-visible"));
    return;
  }
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12 });
  nodes.forEach((node) => observer.observe(node));
}

function setAssetLink(anchorId, nameId, asset, fallbackText) {
  const anchor = byId(anchorId);
  const name = byId(nameId);
  if (!anchor || !name) return;
  if (!asset || !asset.url) {
    name.textContent = fallbackText;
    anchor.classList.add("disabled");
    anchor.setAttribute("aria-disabled", "true");
    anchor.href = "#";
    return;
  }
  name.textContent = asset.name;
  anchor.classList.remove("disabled");
  anchor.removeAttribute("aria-disabled");
  anchor.href = asset.url;
}

function pickAssets(assets) {
  const list = Array.isArray(assets) ? assets : [];
  return {
    win: list.find((asset) => /win(dows)?|\.exe|_windows\.zip/i.test(asset.name || "")),
    mac: list.find((asset) => /mac|\.dmg|_mac\.zip/i.test(asset.name || "")),
  };
}

async function fetchManifest() {
  const response = await fetch("./api/release-manifest.json", { cache: "no-store" });
  if (!response.ok) throw new Error(`manifest status ${response.status}`);
  return response.json();
}

async function fetchGithubFallback() {
  const repo = "tongxigogo-crypto/foreign-trade-assistant";
  const response = await fetch(`https://api.github.com/repos/${repo}/releases/latest`, { cache: "no-store" });
  if (!response.ok) throw new Error(`github status ${response.status}`);
  const data = await response.json();
  return {
    version: data.tag_name || "unavailable",
    assets: (data.assets || []).map((asset) => ({ name: asset.name, url: asset.browser_download_url })),
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
  if (versionNode) versionNode.textContent = manifest.version || "unavailable";
  const { win, mac } = pickAssets(manifest.assets || []);
  setAssetLink("win-download", "win-asset-name", win, "unavailable");
  setAssetLink("mac-download", "mac-asset-name", mac, "unavailable");
}

function getFontShorthand(element) {
  const style = window.getComputedStyle(element);
  return `${style.fontStyle} ${style.fontWeight} ${style.fontSize} ${style.fontFamily}`;
}

function applyPretextBalance(element) {
  const text = element.textContent?.trim();
  if (!text) return;
  const style = window.getComputedStyle(element);
  const lineHeight = Number.parseFloat(style.lineHeight) || Number.parseFloat(style.fontSize) * 1.08;
  const font = getFontShorthand(element);
  const prepared = prepareWithSegments(text, font);
  const natural = measureNaturalWidth(prepared);
  const available = element.parentElement?.clientWidth || natural;
  const targetLines = 2;
  let low = Math.min(available, natural * 0.45);
  let high = Math.min(available, natural);
  let best = high;
  for (let i = 0; i < 18; i += 1) {
    const width = (low + high) / 2;
    const stats = measureLineStats(prepared, width);
    if (stats.lineCount > targetLines) {
      low = width;
    } else {
      best = width;
      high = width;
    }
  }
  const finalWidth = Math.min(available, Math.max(best, Math.min(available, natural * 0.58)));
  element.style.maxWidth = `${finalWidth}px`;
  element.style.minHeight = `${lineHeight * targetLines}px`;
}

async function initPretext() {
  const targets = [...document.querySelectorAll("[data-pretext]")];
  if (!targets.length) return;
  if (document.fonts?.ready) await document.fonts.ready;
  const run = () => targets.forEach((target) => applyPretextBalance(target));
  run();
  let resizeTimer;
  window.addEventListener("resize", () => {
    window.clearTimeout(resizeTimer);
    resizeTimer = window.setTimeout(run, 100);
  });
}

function init() {
  const lang = localStorage.getItem("ta_lang") || "zh";
  applyLang(lang);
  setFooterYear();
  revealSections();
  const toggle = byId("lang-toggle");
  if (toggle) {
    toggle.addEventListener("click", () => {
      const next = (localStorage.getItem("ta_lang") || "zh") === "zh" ? "en" : "zh";
      applyLang(next);
      window.setTimeout(() => { initPretext(); }, 40);
    });
  }
  initDownloadPage();
  initPretext();
}

init();
