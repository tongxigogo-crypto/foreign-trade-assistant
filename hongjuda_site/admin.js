let state = {};
let activeTab = "hero";

const editor = document.getElementById("editor");
const statusNode = document.getElementById("status");

function setStatus(message, isError = false) {
  statusNode.textContent = message;
  statusNode.style.color = isError ? "#b42318" : "#0f4c3a";
}

async function loadContent() {
  const response = await fetch("./content/site-content.json", { cache: "no-store" });
  state = await response.json();
  render();
}

function field(label, path, type = "text") {
  const value = get(path) || "";
  const tag = type === "textarea" ? "textarea" : "input";
  const attr = type === "textarea" ? "rows=\"4\"" : "type=\"text\"";
  return `<label>${label}<${tag} ${attr} data-path="${path}">${escapeHtml(value)}</${tag}></label>`;
}

function get(path) {
  return path.split(".").reduce((value, key) => value && value[key], state);
}

function set(path, value) {
  const keys = path.split(".");
  let target = state;
  while (keys.length > 1) {
    const key = keys.shift();
    target[key] = target[key] || {};
    target = target[key];
  }
  target[keys[0]] = value;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#039;"
  })[char]);
}

function render() {
  document.querySelectorAll("[data-tab]").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.tab === activeTab);
  });
  if (activeTab === "hero") renderHero();
  if (activeTab === "products") renderCollection("products", ["name", "category", "summary", "image"]);
  if (activeTab === "cases") renderCollection("cases", ["title", "location", "product", "result", "image"]);
  if (activeTab === "faq") renderCollection("faq", ["question", "answer"]);
  if (activeTab === "json") renderJson();
}

function renderHero() {
  editor.innerHTML = `
    <div class="editor-list">
      <div class="field-grid">
        ${field("公司中文名", "company.name_zh")}
        ${field("公司英文名", "company.name_en")}
        ${field("联系邮箱", "company.email")}
        ${field("联系电话", "company.phone")}
      </div>
      ${field("首屏定位", "hero.kicker")}
      ${field("首屏标题", "hero.title", "textarea")}
      ${field("首屏说明", "hero.subtitle", "textarea")}
      ${field("首屏图片路径", "hero.image")}
      <label>上传首屏图片<input type="file" data-upload-path="hero.image" accept="image/*"></label>
    </div>
  `;
}

function renderCollection(key, fields) {
  const rows = state[key] || [];
  editor.innerHTML = `
    <div class="editor-list">
      ${rows.map((item, index) => `
        <article class="row-card">
          <strong>${key} #${index + 1}</strong>
          <div class="field-grid">
            ${fields.map((name) => {
              const label = name === "image" ? "图片路径" : name;
              const type = ["summary", "result", "answer"].includes(name) ? "textarea" : "text";
              return field(label, `${key}.${index}.${name}`, type);
            }).join("")}
          </div>
          ${fields.includes("image") ? `<label>上传图片<input type="file" data-upload-path="${key}.${index}.image" accept="image/*"></label>` : ""}
        </article>
      `).join("")}
    </div>
  `;
}

function renderJson() {
  editor.innerHTML = `<label>完整内容 JSON<textarea id="json-editor" rows="26">${escapeHtml(JSON.stringify(state, null, 2))}</textarea></label>`;
}

async function upload(file) {
  const buffer = await file.arrayBuffer();
  let binary = "";
  new Uint8Array(buffer).forEach((value) => { binary += String.fromCharCode(value); });
  const response = await fetch("/api/assets", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ filename: file.name, content_base64: btoa(binary) })
  });
  if (!response.ok) throw new Error("upload failed");
  return response.json();
}

document.addEventListener("click", (event) => {
  const tab = event.target.closest("[data-tab]");
  if (!tab) return;
  activeTab = tab.dataset.tab;
  render();
});

document.addEventListener("input", (event) => {
  const input = event.target.closest("[data-path]");
  if (input) set(input.dataset.path, input.value);
  const json = event.target.closest("#json-editor");
  if (json) {
    try {
      state = JSON.parse(json.value);
      setStatus("JSON 已解析，点击保存后写入文件。");
    } catch {
      setStatus("JSON 格式暂时无效。", true);
    }
  }
});

document.addEventListener("change", async (event) => {
  const input = event.target.closest("[data-upload-path]");
  if (!input || !input.files?.[0]) return;
  try {
    setStatus("正在上传图片...");
    const result = await upload(input.files[0]);
    set(input.dataset.uploadPath, result.path);
    setStatus(`图片已上传：${result.path}`);
    render();
  } catch {
    setStatus("图片上传失败。请确认通过 local_server.py 打开后台。", true);
  }
});

document.getElementById("save").addEventListener("click", async () => {
  try {
    const response = await fetch("/api/content", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(state)
    });
    if (!response.ok) throw new Error("save failed");
    state = await response.json();
    setStatus("已保存到 content/site-content.json。");
    render();
  } catch {
    const blob = new Blob([JSON.stringify(state, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "site-content.json";
    link.click();
    URL.revokeObjectURL(url);
    setStatus("当前不是本地保存服务器，已改为下载 JSON 备份。", true);
  }
});

document.getElementById("download").addEventListener("click", () => {
  const blob = new Blob([JSON.stringify(state, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "site-content.json";
  link.click();
  URL.revokeObjectURL(url);
});

document.getElementById("import").addEventListener("change", async (event) => {
  const file = event.target.files?.[0];
  if (!file) return;
  state = JSON.parse(await file.text());
  setStatus("JSON 已导入，点击保存后写入内容文件。");
  render();
});

loadContent();
