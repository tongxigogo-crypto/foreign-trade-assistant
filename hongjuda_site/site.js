(async function () {
  const response = await fetch("./content/site-content.json", { cache: "no-store" }).catch(() => null);
  if (!response || !response.ok) return;
  const content = await response.json();

  function get(path) {
    return path.split(".").reduce((value, key) => value && value[key], content);
  }

  document.querySelectorAll("[data-bind]").forEach((node) => {
    const value = get(node.dataset.bind);
    if (typeof value === "string" && value) node.textContent = value;
  });
  document.querySelectorAll("[data-image]").forEach((node) => {
    const value = get(node.dataset.image);
    if (typeof value === "string" && value) node.src = value;
  });

  const products = document.querySelector("[data-products]");
  if (products && Array.isArray(content.products)) {
    products.innerHTML = content.products.map((item) => `
      <article class="product-card">
        <img src="${item.image}" alt="${item.name}">
        <div>
          <small>${item.category}</small>
          <h3>${item.name}</h3>
          <p>${item.summary}</p>
        </div>
      </article>
    `).join("");
  }

  const cases = document.querySelector("[data-cases]");
  if (cases && Array.isArray(content.cases)) {
    cases.innerHTML = content.cases.map((item) => `
      <article class="case-card">
        <img src="${item.image}" alt="${item.title}">
        <div>
          <small>${item.location}</small>
          <h3>${item.title}</h3>
          <p><strong>Product:</strong> ${item.product}</p>
          <p>${item.result}</p>
        </div>
      </article>
    `).join("");
  }

  const faq = document.querySelector("[data-faq]");
  if (faq && Array.isArray(content.faq)) {
    faq.innerHTML = content.faq.map((item) => `
      <article>
        <h3>${item.question}</h3>
        <p>${item.answer}</p>
      </article>
    `).join("");
  }

  const form = document.querySelector("[data-contact-form]");
  const status = document.querySelector("[data-form-status]");
  form?.addEventListener("submit", (event) => {
    event.preventDefault();
    const payload = Object.fromEntries(new FormData(form).entries());
    const rows = JSON.parse(localStorage.getItem("hongjuda_inquiry_drafts") || "[]");
    rows.unshift({ ...payload, created_at: new Date().toISOString() });
    localStorage.setItem("hongjuda_inquiry_drafts", JSON.stringify(rows.slice(0, 30)));
    status.textContent = "Inquiry draft saved locally. Connect a production form endpoint before launch.";
    form.reset();
  });
}());
