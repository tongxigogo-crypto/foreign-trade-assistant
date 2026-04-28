from __future__ import annotations

import copy
import re
from html import escape
from typing import Callable

IMAGE_PATH_FIXUPS = {
    "./灏廞鍜岃眴瀛?璞嗗瓙鎰熻阿.png": "./小Q和豆子/豆子感谢.png",
    "./灏廞鍜岃眴瀛?APP.png": "./小Q和豆子/APP.png",
    "./灏廞鍜岃眴瀛?灏廞浠嬬粛.png": "./小Q和豆子/小Q介绍.png",
}

V66_DEFAULT_CONTENT = {
    "strings": {
        "zh": {
            "brand_name": "Tong Studio",
            "brand_tagline": "Trade Assistant APP",
            "hero_intro": "汇聚邮件、合同、报价与客户记录，把外贸人的经验沉淀成一个本地优先的私有工作台。",
            "hero_subtitle": "敏感资料默认本地处理，不用于云端训练；每一次回复，都更贴近你的业务语境和谈判风格。",
            "hero_bridge": "不再是多一个工具，而是把所有文件同步在一个系统。",
            "hero_summary_title": "不再翻找，即刻响应",
            "hero_summary_body": "外贸助理把客户上下文、产品资料、报价历史和模型记忆收回同一个本地优先系统，让每一次跟进都从完整记录开始。",
            "pet_ip_title": "懂<span class=\"title-accent\">代码</span>，也懂<span class=\"title-accent\">IP</span>",
            "pet_ip_body": "小Q和豆子不是装饰角色，而是 Tong工作室 的品牌记忆点：一个负责温柔兜底，一个负责制造戏剧感，让技术能力更容易被记住。",
            "trade_assistant_title": "客户上下文快速恢复",
            "trade_assistant_body": "系统自动汇总历史沟通、产品信息、报价历史，消息许久的客户再联系，一键查看所有沟通记录。",
            "pet_trade_title": "报价与回复",
            "pet_trade_body": "从询盘到报价，不只是数字，会连同 MOQ、SKU 资料、客户阶段和跟进建议一起生成，让每次回复都保持你自己的风格。",
            "mini_program_title": "模型灵活性",
            "mini_program_body": "不用再担心 AI 的更新，随时随地更换 AI，都可以立刻恢复全部记忆。",
            "contact_title": "现在，<span>投喂你的项目吧！</span>",
            "contact_body": "",
        },
        "en": {},
    },
    "images": {
        "home.hero": "./小Q和豆子/豆子感谢.png",
        "home.trade_assistant": "./小Q和豆子/APP.png",
        "home.pet_trade": "./小Q和豆子/小Q介绍.png",
        "home.mini_program": "./小Q和豆子/豆子感谢.png",
    },
    "pet_products_gallery": {
        "cards": [
            {
                "id": "mother-keepsake",
                "image": "./pet-product-assets/custom-dog-keepsake-poster.png",
                "cover_label": "儿童手绘定制",
                "cover_title": "妈妈项链",
                "title": "把孩子画里的妈妈戴在身边",
                "summary": "儿童手绘变成18K镀金珐琅项链，适合作为家庭纪念礼物。",
                "tag": "18K / 珐琅 / 定制",
                "status": "live",
                "entry_mode": "template",
            },
            {
                "id": "pet-keepsake",
                "image": "./pet-product-assets/custom-dog-keepsake-poster.png",
                "cover_label": "宠物纪念",
                "cover_title": "童年",
                "title": "把孩子的童年戴在身边",
                "summary": "孩子画的小狗变成纪念项链，把宠物陪伴和家庭记忆做成产品故事。",
                "tag": "宠物 / 纪念 / 礼物",
                "status": "live",
                "entry_mode": "template",
            },
            {
                "id": "dog-photo-keepsake",
                "image": "./pet-product-assets/custom-dog-keepsake-poster.png",
                "cover_label": "实拍样品",
                "cover_title": "宠物",
                "title": "把手绘宠物变成可佩戴纪念",
                "summary": "从儿童画到吊坠成品，适合宠物纪念、亲子礼物和定制饰品展示。",
                "tag": "手绘 / 宠物",
                "status": "coming_soon",
                "entry_mode": "none",
            },
            {
                "id": "hero-keepsake",
                "image": "./pet-product-assets/custom-dog-keepsake-poster.png",
                "cover_label": "英雄定制",
                "cover_title": "愿望",
                "title": "把孩子想成为的人戴在身边",
                "summary": "手绘英雄形象转成项链，把一句童年愿望做成长期陪伴的礼物。",
                "tag": "英雄 / 定制",
                "status": "coming_soon",
                "entry_mode": "none",
            },
        ],
    },
    "pet_product_template": {
        "path": "./pet-product-template.html",
        "eyebrow": "Pet Product Template",
        "title": "宠物用品内容模板",
        "intro": "先用一套统一模板承接后续内容，等后台内容稳定后，再扩展成独立详情页。",
        "status_label": "模板预览",
        "cta_label": "联系询盘",
        "cta_url": "mailto:tongxigogo@gmail.com",
        "sections": {
            "story_title": "产品故事",
            "story_body": "这里放产品定位、材质选择和适用场景，保持品牌气质与业务信息一起出现。",
            "spec_title": "规格与沟通点",
            "spec_body": "这里放 MOQ、尺寸、五金、包装等适合外贸询盘使用的关键信息。",
            "use_case_title": "使用场景",
            "use_case_body": "这里放宠物使用环境、用户感知和后续图文素材建议。",
            "care_title": "保养与沟通补充",
            "care_body": "这里放清洗方式、使用注意事项和售前沟通补充。",
        },
        "specs": [
            {"label": "MOQ", "value": "300 sets"},
            {"label": "Material", "value": "Editorial placeholder"},
            {"label": "Packaging", "value": "Flat pack ready"},
        ],
        "seo": {
            "title": "Tong Studio | 宠物用品内容模板",
            "description": "用于后续发布胸背带、牵引绳、玩具选品和窝垫布艺等宠物用品内容页。",
            "canonical_path": "/pet-product-template.html",
        },
    },
}


def _replace(pattern: str, html: str, replacement: str, flags: int = re.S) -> str:
    return re.sub(pattern, replacement, html, count=1, flags=flags)


def _replace_nth(pattern: str, html: str, replacer: Callable[[re.Match[str]], str], index: int, flags: int = re.S) -> str:
    matches = list(re.finditer(pattern, html, flags))
    if index >= len(matches):
        return html
    match = matches[index]
    return html[: match.start()] + replacer(match) + html[match.end() :]


def extract_content(html: str) -> dict:
    return copy.deepcopy(V66_DEFAULT_CONTENT)


def _gallery_status_markup(status: str, entry_mode: str, template_path: str, card_id: str) -> str:
    if status == "live" and entry_mode == "template":
        href = f"{template_path}#{escape(card_id)}"
        return f'<a class="pet-gallery-link" href="{href}"><span>View poster</span><span>&rarr;</span></a>'
    if status == "live":
        return '<span class="pet-gallery-link is-coming"><span>Live</span><span>&middot;</span></span>'
    return '<span class="pet-gallery-link is-coming"><span>Coming soon</span><span>&middot;</span></span>'

def _gallery_card_markup(card: dict, index: int, template_path: str) -> str:
    shape_a_styles = [
        "",
        ' style="background: radial-gradient(circle at 40% 40%, rgba(14,165,233,0.48), rgba(14,165,233,0.08));"',
        ' style="background: radial-gradient(circle at 40% 40%, rgba(167,139,250,0.48), rgba(167,139,250,0.08));"',
        ' style="background: radial-gradient(circle at 40% 40%, rgba(34,197,94,0.42), rgba(34,197,94,0.08));"',
    ]
    shape_b_styles = [
        "",
        ' style="background: radial-gradient(circle at 50% 50%, rgba(45,212,191,0.34), rgba(45,212,191,0.06));"',
        ' style="background: radial-gradient(circle at 50% 50%, rgba(236,72,153,0.28), rgba(236,72,153,0.06));"',
        ' style="background: radial-gradient(circle at 50% 50%, rgba(59,130,246,0.24), rgba(59,130,246,0.06));"',
    ]
    shape_a = shape_a_styles[index] if index < len(shape_a_styles) else ""
    shape_b = shape_b_styles[index] if index < len(shape_b_styles) else ""
    status_markup = _gallery_status_markup(
        card.get("status", "coming_soon"),
        card.get("entry_mode", "none"),
        template_path,
        card.get("id", f"card-{index + 1}"),
    )
    return f"""
                        <article class="pet-gallery-card">
                            <div class="pet-gallery-cover">
                                <img class="pet-gallery-image" src="{escape(card.get("image", ""))}" alt="{escape(card.get("title", ""))} cover image" loading="lazy" decoding="async">
                                <div class="pet-gallery-shape a"{shape_a}></div>
                                <div class="pet-gallery-shape b"{shape_b}></div>
                                <div class="pet-gallery-shape c"></div>
                                <div class="pet-gallery-layout">
                                    <div class="pet-gallery-cover-chip">{escape(card.get("cover_label", ""))}</div>
                                    <div class="pet-gallery-number">{index + 1:02d}</div>
                                    <div class="pet-gallery-cover-title">{escape(card.get("cover_title", ""))}</div>
                                </div>
                            </div>
                            <div class="pet-gallery-copy">
                                <h3 class="use-pretext" style="color: #0F172A;">{escape(card.get("title", ""))}</h3>
                                <p class="use-pretext" style="color: #64748b;">{escape(card.get("summary", ""))}</p>
                                <div class="pet-gallery-footer">
                                    <div class="pet-gallery-tag">{escape(card.get("tag", ""))}</div>
                                    {status_markup}
                                </div>
                            </div>
                        </article>"""


def apply_content(html: str, content: dict) -> str:
    strings = content.get("strings", {})
    zh = strings.get("zh", {})
    en = strings.get("en", {})
    primary = en if any(str(value).strip() for value in en.values()) else zh
    raw_images = content.get("images", {})
    images = {key: IMAGE_PATH_FIXUPS.get(value, value) for key, value in raw_images.items()}
    gallery = copy.deepcopy(V66_DEFAULT_CONTENT["pet_products_gallery"])
    incoming_gallery = content.get("pet_products_gallery", {})
    incoming_cards = (
        incoming_gallery.get("en", {}).get("cards")
        or incoming_gallery.get("zh", {}).get("cards")
        or incoming_gallery.get("cards", [])
    )
    for index, card in enumerate(gallery["cards"]):
        if index < len(incoming_cards) and isinstance(incoming_cards[index], dict):
            card.update(incoming_cards[index])
            if card.get("image"):
                card["image"] = IMAGE_PATH_FIXUPS.get(card["image"], card["image"])
    template = copy.deepcopy(V66_DEFAULT_CONTENT["pet_product_template"])
    incoming_template = content.get("pet_product_template", {})
    template.update({key: value for key, value in incoming_template.items() if key not in {"sections", "seo"}})
    template["sections"].update(incoming_template.get("sections", {}))
    template["seo"].update(incoming_template.get("seo", {}))

    html = _replace(
        r'(<div class="text-2xl font-black tracking-tighter text-gray-900">)(.*?)(</div>)',
        html,
        rf"\1{primary.get('brand_name', '')}\3",
    )
    html = _replace(
        r'(<div class="text-\[10px\] font-bold uppercase tracking-\[0\.28em\] text-slate-400">)(.*?)(</div>)',
        html,
        rf"\1{primary.get('brand_tagline', '')}\3",
    )
    html = _replace(
        r'(<h1 class="(?:use-pretext )?text-5xl md:text-\[4\.4rem\] font-black mb-6 tracking-tighter leading-\[1\.06\]" style="color: #0F172A;" aria-label=")(.*?)(">)(.*?)(</h1>)',
        html,
        rf"\1{escape(primary.get('hero_summary_title', '').replace('<br>', ' '))}\3{primary.get('hero_summary_title', '')}\5",
    )
    html = _replace(
        r'(<p class="hero-copy">)(.*?)(</p>)',
        html,
        rf"\1{primary.get('hero_intro', '')}\3",
    )
    html = _replace(
        r'(<p class="hero-subtitle">)(.*?)(</p>)',
        html,
        rf"\1{primary.get('hero_subtitle', '')}\3",
    )
    html = _replace(
        r'(<h2 class="use-pretext text-5xl md:text-6xl font-black tracking-tighter mb-6" style="color: #0F172A;">)(.*?)(</h2>)',
        html,
        rf"\1{primary.get('hero_bridge', '')}\3",
    )
    html = _replace(
        r'(<p class="use-pretext text-xl font-medium max-w-3xl mx-auto" style="color: #64748b; line-height: 1\.8;">)(.*?)(</p>)',
        html,
        rf"\1{primary.get('hero_summary_body', '')}\3",
    )

    h3_pattern = r'(<h3 class="use-pretext text-2xl font-bold mb-4" style="color: #0F172A;">)(.*?)(</h3>)'
    p_pattern = r'(<p class="use-pretext text-sm" style="color: #64748b; line-height: 1\.8;">)(.*?)(</p>)'
    feature_titles = [primary.get("trade_assistant_title", ""), primary.get("pet_trade_title", ""), primary.get("mini_program_title", "")]
    feature_bodies = [primary.get("trade_assistant_body", ""), primary.get("pet_trade_body", ""), primary.get("mini_program_body", "")]
    for idx, title in enumerate(feature_titles):
        html = _replace_nth(h3_pattern, html, lambda m, title=title: f"{m.group(1)}{title}{m.group(3)}", idx)
    for idx, body in enumerate(feature_bodies):
        html = _replace_nth(p_pattern, html, lambda m, body=body: f"{m.group(1)}{body}{m.group(3)}", idx)

    html = _replace(
        r'(<section id="pet-ip".*?<h2 class="(?:use-pretext )?text-5xl font-black tracking-tighter mb-6" style="color: #0F172A;">)(.*?)(</h2>)',
        html,
        rf"\1{primary.get('pet_ip_title', '')}\3",
    )
    html = _replace(
        r'(<section id="pet-ip".*?<p class="use-pretext text-xl font-medium max-w-2xl mx-auto" style="color: #64748b;">)(.*?)(</p>)',
        html,
        rf"\1{primary.get('pet_ip_body', '')}\3",
    )
    html = _replace(
        r'(<section id="contact".*?<h2 class="contact-feed-title relative z-10" data-contact-title>)(.*?)(</h2>)',
        html,
        rf"\1{primary.get('contact_title', '')}\3",
    )

    local_img_pattern = r'(<img[^>]+src=")(\.\/[^"]+)("[^>]*>)'
    slots = [
        images.get("home.hero", V66_DEFAULT_CONTENT["images"]["home.hero"]),
        images.get("home.trade_assistant", V66_DEFAULT_CONTENT["images"]["home.trade_assistant"]),
        images.get("home.pet_trade", V66_DEFAULT_CONTENT["images"]["home.pet_trade"]),
        images.get("home.mini_program", V66_DEFAULT_CONTENT["images"]["home.mini_program"]),
    ]
    for idx, src in enumerate(slots):
        html = _replace_nth(local_img_pattern, html, lambda m, src=src: f'{m.group(1)}{src}{m.group(3)}', idx)

    gallery_markup = "\n".join(
        _gallery_card_markup(card, index, template.get("path", "./pet-product-template.html"))
        for index, card in enumerate(gallery["cards"])
    )
    html = _replace(
        r'(<div class="pet-gallery-row">)(.*?)(</div>\s*<div class="pet-gallery-note">)',
        html,
        rf"\1{gallery_markup}\3",
    )

    return html


PREVIEW_SCRIPT = """
<script>
(() => {
  const params = new URLSearchParams(window.location.search);
  if (params.get("preview") !== "1") return;
  const raw = window.localStorage.getItem("site_content_preview");
  if (!raw) return;
  let payload;
  try { payload = JSON.parse(raw); } catch { return; }
  const strings = payload?.strings || {};
  const zh = strings?.zh || {};
  const en = strings?.en || {};
  const primary = Object.values(en).some((value) => String(value || "").trim()) ? en : zh;
  const images = payload?.images || {};
  const gallery = payload?.pet_products_gallery?.cards || [];
  const templatePath = payload?.pet_product_template?.path || './pet-product-template.html';
  const setHtml = (selector, value, index = 0) => {
    const nodes = document.querySelectorAll(selector);
    const node = nodes[index];
    if (node && value) node.innerHTML = value;
  };
  const setText = (selector, value, index = 0) => {
    const nodes = document.querySelectorAll(selector);
    const node = nodes[index];
    if (node && value) node.textContent = value;
  };
  const setSrc = (selector, value, index = 0) => {
    const nodes = document.querySelectorAll(selector);
    const node = nodes[index];
    if (node && value) node.src = value;
  };
  setText('nav .text-2xl.font-black', primary.brand_name);
  setText('nav .text-\\[10px\\].font-bold', primary.brand_tagline);
  setHtml('#sc-chaos h1', primary.hero_summary_title);
  setText('#sc-chaos .hero-copy', primary.hero_intro);
  setText('#sc-chaos .hero-subtitle', primary.hero_subtitle);
  setHtml('#features h2.use-pretext', primary.hero_bridge);
  setHtml('#features .text-xl.font-medium', primary.hero_summary_body);
  setText('#features h3.use-pretext', primary.trade_assistant_title, 0);
  setText('#features h3.use-pretext', primary.pet_trade_title, 1);
  setText('#features h3.use-pretext', primary.mini_program_title, 2);
  setText('#features p.use-pretext.text-sm', primary.trade_assistant_body, 0);
  setText('#features p.use-pretext.text-sm', primary.pet_trade_body, 1);
  setText('#features p.use-pretext.text-sm', primary.mini_program_body, 2);
  setHtml('#pet-ip h2', primary.pet_ip_title);
  setText('#pet-ip p.use-pretext.text-xl', primary.pet_ip_body);
  setHtml('#contact [data-contact-title]', primary.contact_title);
  setSrc('.core-avatar', images['home.hero']);
  setSrc('.workspace-shot img', images['home.trade_assistant']);
  setSrc('.ip-card-portrait img', images['home.pet_trade'], 0);
  setSrc('.ip-card-portrait img', images['home.mini_program'], 1);
  gallery.forEach((card, index) => {
    setSrc('#pet-products-gallery .pet-gallery-image', card.image, index);
    setText('#pet-products-gallery .pet-gallery-cover-chip', card.cover_label, index);
    setText('#pet-products-gallery .pet-gallery-cover-title', card.cover_title, index);
    setText('#pet-products-gallery .pet-gallery-copy h3.use-pretext', card.title, index);
    setText('#pet-products-gallery .pet-gallery-copy p.use-pretext', card.summary, index);
    setText('#pet-products-gallery .pet-gallery-tag', card.tag, index);
    const links = document.querySelectorAll('#pet-products-gallery .pet-gallery-footer .pet-gallery-link');
    const node = links[index];
    if (!node) return;
    if (card.status === 'live' && (card.entry_mode || 'none') === 'template') {
      if (node.tagName === 'A') {
        node.classList.remove('is-coming');
        node.setAttribute('href', `${templatePath}#${card.id || `card-${index + 1}`}`);
        node.innerHTML = '<span>Live</span><span>→</span>';
      } else {
        const replacement = document.createElement('a');
        replacement.className = 'pet-gallery-link';
        replacement.href = `${templatePath}#${card.id || `card-${index + 1}`}`;
        replacement.innerHTML = '<span>Live</span><span>→</span>';
        node.replaceWith(replacement);
      }
      return;
    }
    if (card.status === 'live') {
      if (node.tagName === 'A') {
        const replacement = document.createElement('span');
        replacement.className = 'pet-gallery-link is-coming';
        replacement.innerHTML = '<span>Live</span><span>·</span>';
        node.replaceWith(replacement);
      } else {
        node.classList.add('is-coming');
        node.innerHTML = '<span>Live</span><span>·</span>';
      }
      return;
    }
    if (node.tagName === 'A') {
      const replacement = document.createElement('span');
      replacement.className = 'pet-gallery-link is-coming';
      replacement.innerHTML = '<span>Coming soon</span><span>·</span>';
      node.replaceWith(replacement);
    } else {
      node.classList.add('is-coming');
      node.innerHTML = '<span>Coming soon</span><span>·</span>';
    }
  });
})();
</script>
"""
