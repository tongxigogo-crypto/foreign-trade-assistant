from __future__ import annotations

import copy
import re
from typing import Callable


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


def apply_content(html: str, content: dict) -> str:
    zh = content.get("strings", {}).get("zh", {})
    images = content.get("images", {})

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
})();
</script>
"""

