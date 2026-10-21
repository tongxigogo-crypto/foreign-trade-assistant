# AI Trade Multi-Agent System

[![ci](https://github.com/tongxigogo-crypto/foreign-trade-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/tongxigogo-crypto/foreign-trade-assistant/actions/workflows/ci.yml)

一个用 Python 写的多 Agent 外贸业务工作台。核心思路不是"让一个大模型什么都干"，
而是把外贸流程拆成一组有明确职责的 Agent，由编排器按业务事件调度，规则和数据放在文件里而不是提示词里。

如果你熟悉 RAG 或知识库驱动的系统，可以把它理解成：**结构化业务规则 + 角色化 Agent + 事件编排**。
不同之处在于这里检索的是本地规则文件（定价、运费、合规），而不是向量库。

## 平台

macOS、Linux、Windows 都可以跑。代码里没有写死任何盘符或绝对路径，
所有路径都来自 `.env` 或相对项目根目录。

```bash
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows PowerShell
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
cp .env.example .env        # Windows: copy .env.example .env
```

## 运行

```bash
python -m app.main
```

## 测试

```bash
python -m pytest -q
```

## Google Workspace 认证（可选）

只有需要读写 Gmail / Drive / Calendar 时才要配。凭据不写进仓库，通过环境变量指向本机文件：

```bash
# macOS / Linux
export GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE="$HOME/.config/gws/credentials.json"

# Windows PowerShell
$env:GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE="$env:USERPROFILE\.config\gws\credentials.json"
```

在 `.env` 里也可以写相对路径，程序按项目根目录解析。

## 产品配件计算器

`product-calculator/` 是一个独立的离线工具：算一套产品要发哪些配件，并检查有没有漏配。
双击 `product-calculator/index.html` 即可使用，不需要服务器、联网或安装。

它不含任何产品数据（设计如此）。填自己的产品规格之前先读
`product-calculator/README.md`；公式确认流程见 `product-calculator/规则说明.md`。

## 结构

```
app/          编排器、契约、实现
agents/       角色定义与职责边界
data/         示例业务数据（客户、定价、运费、合规规则）
trade_ops/    外贸运营输入与输出样例
product-calculator/  独立的配件计算器（HTML + JS，与 Python 部分无依赖）
tests/        自动化测试
skills/       Google Workspace CLI 技能集（见下）
```

## skills/ 的来源

`skills/gws-*` 是由 [`googleworkspace/cli`](https://github.com/googleworkspace/cli) 的
`gws generate-skills` 命令生成的 Google Workspace API 技能文件，
原项目以 **Apache License 2.0** 发布。这里原样保留以便本仓库离线可用，
许可与署名见 `skills/NOTICE.md`。

这些文件是生成物。想自己重新生成：

```bash
gws generate-skills --out ./skills
```

## 数据说明

`data/` 和 `trade_ops/` 里的客户、询盘、产品、价格全部是示例数据，
邮箱使用 `example.com` 域名，公司名和产品名均为虚构，不对应任何真实客户或供应商。

## 已知限制

- 编排器是单进程的，没有做并发写入保护。
- 规则文件改动后需要重启，没有热加载。
- Google 相关 Agent 在未配置凭据时会跳过，不会报错退出。
- 没有做多语言界面。
