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
            "hero_intro": "这不是再包一层 AI 聊天，而是把询盘、报价、邮件和跟进动作拉回同一条业务链路。默认本地优先，必要时再调用云端能力，当前版本已迭代到 v0.1.1-beta2-build39。",
            "hero_bridge": "不是再加一个 AI，而是把外贸动作重新接回同一套工作流。",
            "hero_summary_title": "把客户、报价、邮件和任务<br>收回同一个工作台",
            "hero_summary_body": "客户资料、报价版本、邮件历史、待办任务和相关文件都在同一个 App 内处理，默认本地化保存与调用，不再担心商业内容被云端直接获取。豆子核心继续负责全局避障演示，但页面叙事已经回到真实产品。",
            "pet_ip_title": "产品形象展示",
            "pet_ip_body": "小Q和豆子不是硬塞进来的吉祥物，而是 Tong工作室 的品牌识别锚点，负责把专业能力变得可被记住。",
            "trade_assistant_title": "客户上下文归档",
            "trade_assistant_body": "把客户资料、产品资料和邮件历史归到同一个工作台，老客户隔很久再回来，也不用重新靠记忆拼图。",
            "pet_trade_title": "报价与邮件建议",
            "pet_trade_body": "不只是吐一个数字，而是把 MOQ、SKU、历史语境和跟进建议一起整理出来，减少“报出去就沉海”。",
            "mini_program_title": "任务推进与多模型兼容",
            "mini_program_body": "能本地处理就先本地处理，云模型和本地模型都能接。换模型时，任务和历史链路会继续沿用。",
            "contact_title": "如果你也在做宠物用品外贸，<br>现在可以直接聊工作流和产品方案。",
            "contact_body": "当前外贸助理已迭代到 v0.1.1-beta2-build39。你可以先从询盘分析、报价建议和任务推进聊起，也可以继续展开宠物 IP、工具链和后续供应链准备怎么串起来。",
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
                "id": "harness",
                "image": "./小Q和豆子/小Q介绍.png",
                "cover_label": "Harness Guide",
                "cover_title": "胸背带",
                "title": "胸背带内容位",
                "summary": "后续会补入材质、尺寸、MOQ 与适用场景。",
                "tag": "Material / MOQ",
                "status": "coming_soon",
                "entry_mode": "none",
            },
            {
                "id": "toys",
                "image": "./小Q和豆子/豆子感谢.png",
                "cover_label": "Selection Notes",
                "cover_title": "玩具选品",
                "title": "玩具选品内容位",
                "summary": "后续会补入安全性、材质差异与出口沟通点。",
                "tag": "Selection / SEO",
                "status": "coming_soon",
                "entry_mode": "none",
            },
            {
                "id": "leash",
                "image": "./小Q和豆子/走秀.png",
                "cover_label": "Leash Notes",
                "cover_title": "牵引绳",
                "title": "牵引绳内容位",
                "summary": "后续会补入长度规格、五金方案与包装信息。",
                "tag": "Hardware / Use Case",
                "status": "coming_soon",
                "entry_mode": "none",
            },
            {
                "id": "beds",
                "image": "./小Q和豆子/豆子.png",
                "cover_label": "Bed & Fabric",
                "cover_title": "窝垫布艺",
                "title": "窝垫布艺内容位",
                "summary": "后续会补入布料、填充、清洁方式与场景说明。",
                "tag": "Editorial Shelf",
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
        return f'<a class="pet-gallery-link" href="{href}"><span>已上线</span><span>→</span></a>'
    if status == "live":
        return '<span class="pet-gallery-link is-coming"><span>已上线</span><span>·</span></span>'
    return '<span class="pet-gallery-link is-coming"><span>敬请期待</span><span>·</span></span>'
    if status == "live":
        return '<span class="pet-gallery-link is-coming"><span>已上线</span><span>→</span></span>'
    return '<span class="pet-gallery-link is-coming"><span>敬请期待</span><span>·</span></span>'


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
                                <img class="pet-gallery-image" src="{escape(card.get("image", ""))}" alt="{escape(card.get("title", ""))} 封面图" loading="lazy" decoding="async">
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
    zh = content.get("strings", {}).get("zh", {})
    raw_images = content.get("images", {})
    images = {key: IMAGE_PATH_FIXUPS.get(value, value) for key, value in raw_images.items()}
    gallery = copy.deepcopy(V66_DEFAULT_CONTENT["pet_products_gallery"])
    incoming_gallery = content.get("pet_products_gallery", {})
    for index, card in enumerate(gallery["cards"]):
        incoming_cards = incoming_gallery.get("cards", [])
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
        rf"\1{zh.get('brand_name', '')}\3",
    )
    html = _replace(
        r'(<div class="text-\[10px\] font-bold uppercase tracking-\[0\.28em\] text-slate-400">)(.*?)(</div>)',
        html,
        rf"\1{zh.get('brand_tagline', '')}\3",
    )
    html = _replace(
        r'(<h1 class="use-pretext text-5xl md:text-\[4\.4rem\] font-black mb-6 tracking-tighter leading-\[1\.06\]" style="color: #0F172A;">)(.*?)(</h1>)',
        html,
        rf"\1{zh.get('hero_summary_title', '')}\3",
    )
    html = _replace(
        r'(<p class="use-pretext text-lg max-w-xl mx-auto font-medium leading-relaxed" style="color: #64748b;">)(.*?)(</p>)',
        html,
        rf"\1{zh.get('hero_intro', '')}\3",
    )
    html = _replace(
        r'(<h2 class="use-pretext text-5xl md:text-6xl font-black tracking-tighter mb-6" style="color: #0F172A;">)(.*?)(</h2>)',
        html,
        rf"\1{zh.get('hero_bridge', '')}\3",
    )
    html = _replace(
        r'(<p class="use-pretext text-xl font-medium max-w-3xl mx-auto" style="color: #64748b; line-height: 1\.8;">)(.*?)(</p>)',
        html,
        rf"\1{zh.get('hero_summary_body', '')}\3",
    )

    h3_pattern = r'(<h3 class="use-pretext text-2xl font-bold mb-4" style="color: #0F172A;">)(.*?)(</h3>)'
    p_pattern = r'(<p class="use-pretext text-sm" style="color: #64748b; line-height: 1\.8;">)(.*?)(</p>)'
    feature_titles = [zh.get("trade_assistant_title", ""), zh.get("pet_trade_title", ""), zh.get("mini_program_title", "")]
    feature_bodies = [zh.get("trade_assistant_body", ""), zh.get("pet_trade_body", ""), zh.get("mini_program_body", "")]
    for idx, title in enumerate(feature_titles):
        html = _replace_nth(h3_pattern, html, lambda m, title=title: f"{m.group(1)}{title}{m.group(3)}", idx)
    for idx, body in enumerate(feature_bodies):
        html = _replace_nth(p_pattern, html, lambda m, body=body: f"{m.group(1)}{body}{m.group(3)}", idx)

    html = _replace(
        r'(<section id="pet-ip".*?<h2 class="use-pretext text-5xl font-black tracking-tighter mb-6" style="color: #0F172A;">)(.*?)(</h2>)',
        html,
        rf"\1{zh.get('pet_ip_title', '')}\3",
    )
    html = _replace(
        r'(<section id="pet-ip".*?<p class="use-pretext text-xl font-medium max-w-2xl mx-auto" style="color: #64748b;">)(.*?)(</p>)',
        html,
        rf"\1{zh.get('pet_ip_body', '')}\3",
    )
    html = _replace(
        r'(<section class="py-40 px-8 relative z-20 flex items-center justify-center text-center">.*?<h2 class="use-pretext text-6xl font-black tracking-tighter mb-8 relative z-10" style="color: #0F172A;">)(.*?)(</h2>)',
        html,
        rf"\1{zh.get('contact_title', '')}\3",
    )
    html = _replace(
        r'(<section class="py-40 px-8 relative z-20 flex items-center justify-center text-center">.*?<p class="use-pretext text-xl font-medium mb-16 max-w-2xl mx-auto relative z-10" style="color: #64748b;">)(.*?)(</p>)',
        html,
        rf"\1{zh.get('contact_body', '')}\3",
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
  const zh = payload?.strings?.zh || {};
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
  setText('nav .text-2xl.font-black', zh.brand_name);
  setText('nav .text-\\[10px\\].font-bold', zh.brand_tagline);
  setHtml('#sc-chaos h1.use-pretext', zh.hero_summary_title);
  setHtml('#sc-chaos p.use-pretext', zh.hero_intro);
  setHtml('#features h2.use-pretext', zh.hero_bridge);
  setHtml('#features .text-xl.font-medium', zh.hero_summary_body);
  setText('#features h3.use-pretext', zh.trade_assistant_title, 0);
  setText('#features h3.use-pretext', zh.pet_trade_title, 1);
  setText('#features h3.use-pretext', zh.mini_program_title, 2);
  setText('#features p.use-pretext.text-sm', zh.trade_assistant_body, 0);
  setText('#features p.use-pretext.text-sm', zh.pet_trade_body, 1);
  setText('#features p.use-pretext.text-sm', zh.mini_program_body, 2);
  setText('#pet-ip h2.use-pretext', zh.pet_ip_title);
  setText('#pet-ip p.use-pretext.text-xl', zh.pet_ip_body);
  setHtml('section.py-40 h2.use-pretext', zh.contact_title);
  setHtml('section.py-40 p.use-pretext.text-xl', zh.contact_body);
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
        node.innerHTML = '<span>已上线</span><span>→</span>';
      } else {
        const replacement = document.createElement('a');
        replacement.className = 'pet-gallery-link';
        replacement.href = `${templatePath}#${card.id || `card-${index + 1}`}`;
        replacement.innerHTML = '<span>已上线</span><span>→</span>';
        node.replaceWith(replacement);
      }
      return;
    }
    if (card.status === 'live') {
      if (node.tagName === 'A') {
        const replacement = document.createElement('span');
        replacement.className = 'pet-gallery-link is-coming';
        replacement.innerHTML = '<span>已上线</span><span>·</span>';
        node.replaceWith(replacement);
      } else {
        node.classList.add('is-coming');
        node.innerHTML = '<span>已上线</span><span>·</span>';
      }
      return;
    }
    if (node.tagName === 'A') {
      const replacement = document.createElement('span');
      replacement.className = 'pet-gallery-link is-coming';
      replacement.innerHTML = '<span>敬请期待</span><span>·</span>';
      node.replaceWith(replacement);
    } else {
      node.classList.add('is-coming');
      node.innerHTML = '<span>敬请期待</span><span>·</span>';
    }
  });
})();
</script>
"""
