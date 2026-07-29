# 自我改进 Agent 记忆

此文件仅存储此工作树的持久学习内容。它是有意压缩的：保留应该影响未来工作的规则，而不是完整的运行日志。

## 持久规则

- 在完成实质性运行后记录可复用经验，无需等待用户提出要求。
- 优先记录稳定的项目规则、已纠正的假设和重复出现的失败模式，而不是按时间顺序记录细节。
- 由 orchestrator 负责端到端决策；仅当工作自然拆分为相互独立的策略、内容、SEO、UI、实现、QA、发布或分析任务时，才使用专业子 Agent。
- 将完整的 Agent 注册表视为能力地图，而不是强制执行清单。仅调度任务所需的最少专业 Agent，并报告实际运行的 Agent。
- Self-improvement 必须由证据驱动：先汇总新学到的内容，排除一次性细节；仅当未来执行方式应当改变时，才更新记忆或 harness 规则。
- 根据真实运行增量完善 harness，记录 Agent 选择、任务边界、结构化交接、验证证据，以及确认或失败行为；避免推测性扩展编排架构。
- 小红书组图类任务可采用按需 harness：orchestrator 负责视觉方向与最终整合，`content_agent` 独立产出卡片文案和视频旁白，`qa_agent` 提供发布硬门禁；无需调用完整网站发布角色。为节省生图额度并保持风格统一，可先生成两张 2×2 的 3:4 母版，再用 `ffmpeg` 按精确坐标拆成 8 张独立 3:4 卡片；拆图后必须检查尺寸、文字、正反面逻辑和“概念/非实物”标识。
- 全局应用 `karpathy-style-engineering`：重申目标，选择最小的有效更改，避免推测性重构，并在声明完成之前进行验证。
- `scroll-world` 作为项目级按需 skill 使用：网站任务可采用其完整的预渲染连续镜头与滚动 scrub 引擎；镜头链与原生 9:16 能力通过 `scripts/scroll-world-link.py` 结构化交给 `video_workflow`，网站集成能力可由对方反向调用。先确认 Higgsfield 预算、桌面/原生 9:16 范围和镜头架构，所有接缝必须使用相邻成片的真实边界帧验证，不要把原始场景静帧当作连接端点。
- 未经用户明确确认，请勿在 `site_ops/output/` 下发布、部署或写入。
- 对于此 Windows 计算机上的本地 Remotion 项目，`render`/`still` 可能会挂起，除非 CLI 通过 `--browser-executable="C:\Program Files\Google\Chrome\Application\chrome.exe"`； `@remotion/zod-types@4.0.456` 应与 `zod@4.3.6` 配对，以避免 npm 对等解析循环。
- 对于通过 `python -m http.server` 提供的隔离静态预览，迭代时缓存无效链接 CSS 和 JS (`?v=...`)，并在将过时的视觉行为诊断为代码回归之前验证浏览器中加载的 `href/src`。
- 对于豆子/AI Core等指针拖动UI，合成的`dispatchEvent()`可能无法正确执行指针捕获；使用真实的 Playwright 鼠标移动来验证可拖动行为。
- 将 V6.6 实验转为左导航单视口预览时，在用户的浏览器表观宽度以及标准桌面上进行验证；固定大小的中心合成可能会在宽 Chrome 窗口上留下大的白色区域，除非根 shell 固定到视口并且舞台拥有完整的剩余画布。
- 对于 V6.6 左导航重建，保留原始 `#hero-section` 合约而不是近似它：`min-h-[350vh]`、内部 `sticky top-0 h-screen w-full`、`#impact-1..4` 和 GSAP ScrollTrigger 时间轴必须保留在窗口滚动上。不要将滚动移动到内部容器中，除非使用该滚动器重新配置 ScrollTrigger。
- 对于用户请求的基于 `C:\Users\Administrator\Desktop\preson` 的 V6.6 可视化实验，优先选择 `E:\网页测试\...` 下的独立输出文件夹。保留源 V6.6 文件，仅复制所需的资源，并使用静态 HTML/CSS/JS 实现首屏驾驶舱/应用程序原型，除非明确需要视频渲染或真正的时间轴导出。

## 当前事实来源

- 活动的外部主页来源是 `C:\Users\Administrator\Desktop\preson\indexV6.6_refined.html`。
- 英文独立网站兄弟是 `C:\Users\Administrator\Desktop\preson\indexV6.6_refined_en.html`。
- 共享运行时是 `C:\Users\Administrator\Desktop\preson\bilingual.js`。
- 本地后端/管理源位于 `site_backend/`。
- 当用户查看外部 V6.6 文件时，不要默默地替换 `website_from_playground/` 作为发布目标。
- 保留原始Gemini/原型草稿；将主要迭代写入精炼同级中，除非用户明确要求覆盖。

## 产品及品牌方向

- 该网站为童工作室/童工作室，以现实工作为中心：贸易助理、宠物产品贸易、宠物IP、以及未来的小程序/网站开发服务。
- 避免恢复到通用的 AI SaaS 营销。页面应该保持明亮、软技术、透明、产品叙述和桌面优先。
- 小Q和豆子是品牌记忆资产，不是装饰吉祥物。如果可用，请使用真实的本地图像；不要用字母占位符替换它们。
- 豆子核心是一个漂浮的吉祥物形状的AI核心。保持椭圆形障碍物模型与真实吉祥物轮廓对齐。
- 中英文体验要协调但不完全相同：英文为独立站/Google SEO；未来的中文版本应该是微信友好且以转化为导向的。

## 外部V6.6首页规则

- 保留现有的 GSAP/scrolllytelling shell 和借口交互，除非用户明确要求进行结构重写。
- 第一个屏幕应该感觉像一个真正的贸易助理工作区，而不是通用概念仪表板。
- 第一屏笔记本电脑现在使用全屏 macOS 风格的软件窗口。保留疼痛卡和滚动式过渡；通过 `hero_summary_title`、`hero_intro` 和 `hero_subtitle` 编辑内部窗口副本。
- 将首屏英雄标题保留在一行并附加到 `use-pretext`，以便豆子核心的移动继续影响文本布局。
- 笔记本电脑/工作区面板应显示可信的操作细节：客户背景、查询输入、报价/任务建议、本地优先和多模型兼容性。
- 用户明确授权主动使用子代理并在有用时设计插件/技能；不要等待有关未来设计、文案、SEO、后端或 QA 拆分的提醒。
- 对主要的中间页面部分使用一个共享的外壳宽度；特意将英雄笔记本电脑放在里面。
- 宠物产品库属于宠物 IP 部分，应该感觉像是一个社论/品牌内容栏，而不是正常的产品网格。
- 图库行为：隐藏滚动条水平导轨、温和的自动漂移、悬停/拖动时暂停、支持指针拖动。
- 早期宠物产品卡可以是占位符，但它们必须诚实：使用 `coming_soon` 或模板预览状态，而不是虚假的成品详细链接。
- 当借口损害居中单行排版时，简短的中文显示标题可能会在没有借口的情况下效果更好。

## V6.7 概念方向

- V6.7 概念是 `C:\Users\Administrator\Desktop\preson\indexV6.7_concept.html` 的独立外部原型，而不是直接替代 V6.6。
- 第一个概念阶段仅使用 HyperFrames 作为设计方法：类似合成的场景、时间线思维以及使用普通 HTML/CSS/GSAP/ScrollTrigger 实现的视频风格过渡。
- 在网站概念经过审核、批准并迁移回 V6.6 之前，不要构建实际的 HyperFrames 项目。
- 批准的第一关风格是 v0 / AI 产品发布：浅色画布、软玻璃 UI、蓝色/紫色发光、产品工作区卡、相机推/拉和 UI 重组。
- 第一遍是桌面优先，并使用抽象 UI 占位符；真实应用截图、小Q/豆子资源、宠物产品海报资源等动作方向审核通过后进行连接。
- 启动应该是一个非常短的品牌闪存，大约0.8到1.2秒，而不是一个很长的系统加载序列。
- V6.7 到 V6.6 的迁移应使用启动层增强现有的 V6.6 文件，而不是替换它们：保留 `#global-obstacle`、`data-ai-assistant-mount="douzi-core"`、`.use-pretext` 和 `GlobalPretextEngine`。
- 启动层（`data-v67-launch`、启动、进度、光标、场景点和 `initV67LaunchExperience`）保持中英文 V6.6 页面同步，这样双语导航就不会切换到旧的交互模型。
- 如果 `bilingual.js` 存在 mojibake 或语法损坏，请在可视化迁移之前修复它，因为损坏的运行时可能会阻止语言复制、图库链接处理、联系表单绑定和 `window.TongAICore` 初始化。

## 后端和 CMS 规则

- 最小的可靠后端形状是 Python stdlib WSGI：提供静态外部文件、`/admin`、`/api/content`、资产上传、预览和占位符公共 API，无需添加不必要的框架依赖项。
- 预览/发布必须针对真实的外部 V6.6 文件及其 `content/site-content.json`，而不是断开连接的存储库演示。
- 管理预览应显示草稿与保存状态、图像可达性，并且仅在草稿更改或资产风险警告后才打开预览。
- 当本地预览看起来没有变化时，在假设代码失败之前检查是否有过时的 `site_backend.server` 进程。
- 规范化 Windows/中文路径静态服务：在需要时使用 `latin-1 -> utf-8` 恢复 `PATH_INFO`，并在解析文件之前取消引用。
- 使 `site_backend/v66_adapter.py` 与面向用户的主页/卡片/模板更改保持一致，否则下一个 CMS 保存可能会回归可见的副本和链接。

## 双语 CMS 契约

- 将主页图库卡存储为`pet_products_gallery.zh.cards`和`pet_products_gallery.en.cards`。
- 镜像旧版 `pet_products_gallery.cards` 的中文版本，仅用于向后兼容。
- 前端运行时应该更喜欢本地化的图库卡；只有中文可以回退到旧版 `cards`，否则英文可以继承中文占位符副本。
- 管理员预览目标必须具体：
  - 中文主页：`/?preview=1`
  - 英文主页：`/indexV6.6_refined_en.html?preview=1`
  - 模板页面：`/pet-product-template.html?preview=1`
- 使用`localStorage.site_content_preview`进行草稿预览；它不能覆盖保存的内容。

## SEO 和启动准备

- 对于当前的静态架构，优先考虑直接语义改进而不是框架迁移：标题、描述、规范、JSON-LD、精确的替代文本、咏叹调标签、资源提示和站点地图/机器人。
- 保持首屏豆子和应用图片的优先级；延迟加载首屏 IP/图库资源。
- 英文启动抛光应针对真实可见的 DOM 节点和适配器代码；不要依赖于对历史 mojibake 的宽字符串替换。
- 从实际源字节或解码的 HTTP 响应验证 UTF-8 和 mojibake。 PowerShell 显示可能会产生误导。
- 外部文件回归应尽可能使用稳定的结构标记或英文字符串。

## 宠物产品内容模型

- `pet_products_gallery` 卡目前需要：`id`、`image`、`cover_label`、`cover_title`、`title`、`summary`、`tag`、 `status` 和 `entry_mode`。
- 宠物产品主页资产应位于外部站点资产目录下，目前为 `C:\Users\Administrator\Desktop\preson\pet-product-assets\`，具有稳定的相对 URL，例如 `./pet-product-assets/mother-keepsake-necklace.png`。
- 更改主页图库卡时，一起更新所有三个层：静态 V6.6 HTML 后备、`bilingual.js` 和 `content/site-content.json` 加上 `site_backend/v66_adapter.py` 默认值，否则 CMS 预览/保存可以回归可见主页。
- `status=live` 并不自动意味着该卡应该导航； `entry_mode`控制是否打开共享模板。
- 在生成许多产品页面之前，单个 `pet-product-template.html` 是正确的第一个详细页面支架。
- 模板应保持 CMS 驱动：英雄图像/卡片、眉毛、标题、简介、CTA、规格、部分、注意事项和 SEO 元数据。
- V6.7宠物海报详细信息页面应首先作为静态哈希路由工作：即使`/api/content`不可用，`#mother-keepsake`和`#pet-keepsake`也必须呈现完整的中文后备内容。
- 主页宠物海报导航属于每个活卡的图像和“查看海报”链接。不要使用下方的“打开模板预览”注释作为主要海报路线。
- 如果宠物图库删除了可见的 CTA 按钮，请将 `data-poster-href` 保留在图像封面上，并保留通过 `window.location.href` 的轨道单击处理程序；否则，自动滚动轨道可能会使普通锚点变得不可靠。
- 对于V6.6宠物图库卡体，“仅保留主标题”意味着删除每卡摘要段落和底部CTA/标签行；该卡应仅显示图像加上 `h3`。
- 保持 `site_backend/v66_adapter.py` 和预览运行时与仅标题画廊形状保持一致； CMS 保存后，后端 `apply_content()` 不得重新生成页脚链接、状态丸、标签或卡片摘要。
- 在共享海报页面中保留稳定的 `data-poster-template="v67"` 标记和 `initPosterExperience()` ，以便测试可以将批准的 V6.7 海报体验与早期的通用脚手架区分开来。
- 主页右上角的CTA现在是下载入口，而不是演示预订mailto。将 `data-i18n="navCta"` 文本保留为 `Download` / `下载` 并将其路由到 `./download.html`；下载页面介绍了 InVault / 外贸助理作为本地优先的私人人工智能业务顾问，直到安装程序详细信息准备就绪。
- 当内容/模板发布行为发生变化时，保持 `robots.txt` 和 `sitemap.xml` 同步。

## 联系人和 AI 核心 API

- 豆子AI Core目前是预留助手坐骑，并非即时聊天产品。
- 前端合约：`data-ai-assistant-mount="douzi-core"` 和 `window.TongAICore.context()` / `window.TongAICore.send()`。
- 公共 AI 占位符：
  - `GET /api/ai-context`
  - `POST /api/ai-core/message`
- 在显式添加模型适配器之前，AI 消息端点不得调用外部模型。
- 联系意图段头稳定：
  - `website-development`
  - `mini-program`
  - `product-information`
  - `ip-collaboration`
- 当前联系人端点仅占位符：
  - `POST /api/contact`
  - 验证姓名/联系人/意图/消息
  - 使用蜜罐字段进行简单的垃圾邮件过滤
  - 将接受的主页项目保留到输入中`content/contact-submissions.jsonl`
  - 返回 `feed_saved`
  - 在配置部署凭据之前不发送电子邮件
- 管理员可以通过经过身份验证的 `GET /admin/api/contact-submissions` 和右侧检查器模块查看主页项目提要。
- 电子邮件目标是 `tongxigogo@gmail.com`。
- 微信二维码应使用稳定的资产路径：`小Q和豆子/wechat-qr-tong1390.jpg`。

## 部署方向

- 此项目推荐的免费/低成本形状：Cloudflare Pages + Cloudflare Workers + Resend。
- GitHub Pages 不足以用于真正的表单提交，因为它无法运行 `/api/contact`。
- 部署电子邮件发送应使用环境变量，而不是提交机密：
  - `RESEND_API_KEY`
  - `CONTACT_TO_EMAIL=tongxigogo@gmail.com`
  - `CONTACT_FROM_EMAIL=<verified sender>`
- 如果提交内容变得面向公众且嘈杂，稍后可以使用 Cloudflare Turnstile 添加更强大的垃圾邮件防护。

## 停用或取消优先级的方向

- 除非用户明确要求，否则不要恢复繁重的游戏广场主页方向；目前批准的方向是V6.6 滚动讲述/产品叙述。
- 在内容量和部署需求证明其合理性之前，不要仅仅为了 SEO 而迁移到 Next.js。
- 在共享模板和内容工作流程稳定之前，不要构建许多宠物产品详细信息页面。
- 在最终主页复制、部署和电子邮件发送解决之前，不要将管理 UI 过度构建为完整的 CMS 平台。

## V6.6/V6.7 发布审核学习

- 对于 `C:\Users\Administrator\Desktop\preson` 下的外部静态页面，生产检查必须包括浏览器渲染的移动审核，而不仅仅是文件扫描，因为运行时语言更新可以覆盖静态 HTML。
- 将第五屏宠物图库卡标题保留为正常的 `h3` 文本，而不是 `use-pretext`，因此全局 Pretext 字符引擎始终专注于大型叙事标题，并且不会损坏紧凑的卡标题。
- 公共主页资产应使用 ASCII 部署路径，例如 `characters/douzi-thanks.png`；保持原始中文资产文件夹作为源材料不变，但不重新生成带有中文路径的发布 HTML。
- 将 `InVault Trade Assistant` / `外贸助理` 和 `v0.1.1 Beta` 视为当前公共命名/版本模式，除非用户更改版本名称。
- 当采用外部修复的单文件原型（例如 `geminiV7.1.html`）时，将其复制到新的输出文件夹中并首先迁移其资产目录，然后在 QA 之前将占位卡替换为真实资产。全屏检查必须测量 `main` 和固定的 ScrollTrigger 容器：固定的左侧导航布局应使用 `calc(100vw - var(--left-nav-width))`，而不是 `calc(100% - ...)`，因为 ScrollTrigger 引脚包装器可能会产生水平溢出。
- 可配置的原型参数应该连接到运行时行为，而不仅仅是声明。对于 Gemini V7.1 重建，`window.V66_CONFIG.animation` 驱动启动延迟、英雄冲击规模、滚动长度、APP 演示延迟和图库拖动速度。
- 对于固定的单视口 GSAP 原型，左导航单击应将 GSAP 时间线驱动到固定的场景时间，而不是仅依赖于编程 `window.scrollTo()`。某些浏览器/ScrollTrigger 状态可以更新活动导航而无需实际滚动，从而留下半过渡场景。每次在支持的最短桌面视口中单击导航后，通过检查目标部分 `getBoundingClientRect().y === 0` 进行验证。
- 当修复后的原型简化了原始副本时，请在接受之前与 `indexV6.6_refined.html` 和 `indexV6.6_refined_en.html` 进行比较。保留原始 V6.6 内容合同：功能说明副本、IP 角色描述、4 卡宠物产品导轨、产品说明和完整的联系表单字段。
- `forrestchang/andrej-karpathy-skills` 的实际教训是使实施变更变得轻量、最小化和验证驱动。通过仅修复失败的行为并在总结之前使用具体的浏览器测量/屏幕截图来证明它，从而在此处应用该方法。
- 如果原型迭代偏离了用户的预期基础，请停止修补该分支。将最后批准的基础复制到新的输出文件夹中，保持原始源文件夹不变，并仅应用请求的增量。对于 V6.6 左侧导航任务，正确的增量是：保留 `v66-original-leftnav-rebuild`，将 Gemini 风格的 APP 交互添加到第二个屏幕，并通过本地 `index.html` / `index_en.html` 重新加载公开语言切换，以便干净地重建 Pretext 标题。
- 对于V6.6 Gemini 面板请求，“更换面板”是指英雄序列内打开的笔记本电脑面板`#sc-stable`，而不是整个第二屏幕。保留原始的第二个屏幕，并在运行时仅替换工作台模型（如果这样可以避免接触大型历史 HTML 块）。
- 在左侧导航外壳内放大 V6.6 笔记本电脑/APP 模型时，保留原始 `920 / 592` 笔记本电脑的宽高比，并使用响应式 `width: min(...)`，而不是徒手缩放宽度/高度。验证`documentElement.scrollWidth === viewport width`、`main.right === viewport right`、以及嵌入式APP网格`scrollWidth <= clientWidth`；更改共享面板断点后还会缓存 CSS 链接。
- 对于外部 V6.6 管理适配，保留 `C:\Users\Administrator\Desktop\preson` 的旧版默认后端目标，除非用户明确更改它。新的隔离输出文件夹应由 `SITE_MANAGED_DIR` + `SITE_MANAGED_HTML` 提供服务；如果条目是现代 `index.html`，则将 `content/site-content.json` 和 `/api/content` 视为运行时源，并避免旧的 `apply_content()` HTML 重写，除非显式设置 `SITE_SYNC_HTML=1`。
- 当用户提供非站点可交付路径（例如 `E:\CodexWorkspace`）时，直接在该路径下的同级文件夹中创建最终项目，而不是在 `site-publishing` 内部；如果创建了临时存储库本地文件夹，请将其移出并在最终确定之前验证存储库本地路径不再存在。
- 对移动端曲面产品 3D 的高清文字修复，先分离“源图质量、曲面几何贴合、atlas 有效纹素和压缩”四层证据。若 GLB 已有权威 UV 烘焙文字，不要再叠加单一透明平面；平面会在斜侧或上下环视时悬浮/穿模。优先保留真实曲面 UV，提高 atlas 分辨率与采样质量，并在 KTX2/ETC1S 移动预算内用正面、45°、侧面、背面和上下极限环视做验收。
- 仅把 220px 标签放大并不能证明瓶身文字变清晰；必须同时记录标签母版像素、atlas 中实际涂绘纹素和 KTX2 编码方式。用户肉眼否决 2048/ETC1S 时，优先提高确定性母版和 atlas 有效覆盖，再以 UASTC 清晰版作为上界、最高质量 ETC1S 作为移动体积对照。外部 Blender CLI 若只支持自己的 JSON 场景且不能无损读取现有 `.blend`，不得为了使用新工具而替换项目专用 bpy 烘焙脚本；先核对已安装命令是否与 skill 文档一致。
- 当包装高清原图已丢失且用户授权重新生成时，把精确书法、顶部徽章和底部装饰拆成独立 ImageGen 组件；逐字核对生成文字，规格和厂家小字仍用确定性 SVG。生成组件必须记录提示词摘要、生成方式和 SHA，绿色去背后再组合，不能把 AI 组件标记成非 AI；最终以 Blender 曲面微距与真实网页投影共同验收。
- 对于交互式 PPT 样式的交付成果，默认情况下保持静态页面图像干净，并将戏剧性的“弹出屏幕”效果移动到单击/悬停细节状态。当用户说参考效果是正确的时，请重复使用效果语言，而无需将其烘焙到每个幻灯片背景中。
- 当后续文档仅替换外部 PPT/web-deck 可交付成果的 UI/布局方向时，保留先前批准的交互和资产规则，除非用户明确取消它们。对于汽车科学展板，V3 Apple/Guizang 风格的布局改变了页面构成，而早期的规则仍然控制热点行为、模拟真实照片资源、F1 图像、空气流动和点击触发的弹出细节。
- 对于基于先前静态模板的新公司独立站点构建，更喜欢独立的同级，例如 `hongjuda_site/` 与 `index.html`、`content/site-content.json`、`admin.html`、`local_server.py`、`llms.txt`、`robots.txt`、`sitemap.xml` 和`api/openapi.json`。当架构是产品/公司站点内容而不是宠物/Tong 内容时，请勿重复使用 Tong Studio V6.6 后端适配器；保持本地管理/API stdlib WSGI 和部署静态优先。
- 在启动审核之前，强化本地管理员默认设置：需要 `SITE_ADMIN_PASSWORD` 和 `SITE_ADMIN_SESSION_SECRET`，除非设置了明确的仅本地不安全选择加入，并使用 `utf-8-sig` 读取 CMS JSON/元，以便 Windows 保存的 BOM 文件不会破坏 `/api/content` 或 `/api/ai-context`。
- 对滚动叙事 3D H5 继续开发前，先用实际挂载代码和 E2E 合同校正外部 UI 评审的功能基线；闲置的热点、影片或收尾组件不能仅因评审报告仍提到它们就恢复。全屏桌面画布不得无条件拦截普通滚轮：保留纵向滚动进入后续章节，把 3D 缩放限定为 `Control/Command + 滚轮`，并提供可聚焦画布、方向键环视、`+/-` 缩放、`Home` 复位及读屏说明。资产升级后应同步更新 `verify:glb` 的节点、材质、尺寸和海报合同，避免验收通过但自动验证仍绑定旧模型。
- 为已验收的 3D 产品增加配料“透视开窗”时，优先使用独立离屏渲染层和屏幕空间 `smoothstep` 羽化蒙版，不永久改写基础瓶身材质。桌面鼠标只在瓶身投影区追随；移动端采用延迟长按、向上偏移的窗口、拖动探索和点击固定，并保留五个可聚焦配料按钮。古风背景应使用低对比月庭、宣纸颗粒、远山薄雾和窗棂投影，主体周围保持负空间；低端设备与 reduced-motion 必须降级。
- 当产品已有可复用的配料照片且不需要精确贴合 3D 瓶身轮廓时，单一 DOM 图片层加 CSS 羽化 `mask-image` 是更轻量的首版实现：图片层保持 `pointer-events:none`，手机长按只从材料按钮开始，避免与瓶体旋转和纵向滚动争抢手势。延迟回调不得再次读取 DOM 事件的 `currentTarget`，应在 `pointerdown` 同步缓存控件引用；用伪时钟覆盖 220ms 激活、8px 取消和 ghost click，才能捕获真实浏览器中异步事件对象失效的问题。
