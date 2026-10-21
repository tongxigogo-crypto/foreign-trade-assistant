# 产品算料计算器（引擎 + 界面骨架）

给「客户报一个面积，销售要立刻说出用多少料」这件事用的一套离线工具。

**这个仓库里没有产品数据。** 只有算法、界面骨架，和一份明确标注为虚构的示例定义。
真实的产品规格、费率、型号由使用者自己填。

双击 `index.html` 就能用，不需要服务器、不需要联网、不需要安装任何东西。

## 为什么不含数据

同一个引擎可以算塑木地板、墙板、围栏、门窗、家具、五金。变的是规格和公式，不变的是：

- 输入校验（必填、范围、非数字）
- 逐项取整（含浮点噪声保护）
- 损耗率
- 按单位汇总

把数据抽走之后，这份代码可以开放，而具体的产品规格和报价口径留在各自公司内部。

## 结构

```
index.html                     入口，双击即开
css/app.css                    样式，无框架
js/engine.js                   计算引擎（无 DOM、无数据、无依赖）
js/app.js                      界面控制器（不含任何公式）
data/product-master.example.js 示例产品定义（虚构数据）
data/config.js                 展示层设置（不是计算规则）
tests/offline-smoke-test.cjs   引擎的离线数值验证
规则说明.md                     公式表与改动记录
```

三层职责分得很硬：

| 层 | 允许改什么 | 不允许做什么 |
|---|---|---|
| `engine.js` | 校验、取整、汇总的通用逻辑 | 认识任何具体产品 |
| `product-master.js` | 规格、公式、单位、取整方式 | 碰 DOM |
| `app.js` | 表单、渲染 | 出现任何公式 |

## 换成你自己的产品

1. 复制一份示例，改成自己的文件名：

   ```bash
   cp data/product-master.example.js data/product-master.js
   ```

2. 改 `product-master.js` 里的 `spec`（尺寸、常数）和每个 `items[].compute`（这一项怎么算）。
3. 改 `index.html` 末尾的引用，把 `product-master.example.js` 换成 `product-master.js`。
4. 跑一遍数值验证：

   ```bash
   node tests/offline-smoke-test.cjs
   ```

5. 双击 `index.html`，用一张真实的报价单核对。

`product-master.js` 没有进仓库时页面会提示「产品数据未加载」，不会静默算出一个 0。

## 写一条算料规则

```js
{
  id: 'panel',
  label: '主材板',
  unit: '块',
  rounding: 'ceil',        // ceil | floor | round | none
  overage: 0.03,           // 3% 损耗，和输入里的损耗率是两回事
  note: '面积 ÷ 单板有效覆盖面积',
  compute: function (ctx) {
    return ctx.values.areaM2 / ctx.spec.coveragePerPanelM2;
  }
}
```

`compute(ctx)` 能拿到：

| 字段 | 内容 |
|---|---|
| `ctx.values` | 校验后的数值输入，按输入 id 取 |
| `ctx.spec` | 这个产品的规格对象 |
| `ctx.ceil` / `ctx.floor` / `ctx.round` | 取整函数 |
| `ctx.areaM2(w, l)` | 毫米尺寸换成平方米 |

## 取整为什么要防浮点噪声

`100 / 0.4205 = 237.81`，取整到 238 没问题。
但 `5 / 0.5` 在浮点里可能算出 `10.000000000000002`，直接 `Math.ceil` 会得到 11 块——多一块。
引擎在取整前先减去 `1e-9`，这一项在 `tests/offline-smoke-test.cjs` 里有专门的用例。

## 验收状态

| 项 | 状态 |
|---|---|
| 引擎数值验证（10 条用例） | 通过 |
| `file://` 双击打开渲染 | 通过（Chrome headless 截图核对） |
| 自动填表 + 点击计算 | 通过（100 m² → 250 块 / 1200 个 / 13 支） |
| 真机 / 移动端 | 未做 |
| 真实业务数据核对 | **未做**（仓库内是虚构数据，无法核对） |

最后一行是关键：这份代码证明的是「骨架能跑」，不是「算得对」。
算得对不对于是取决于你填进去的规格和公式，以及有没有拿真实报价单逐项对过。

## 许可

MIT。示例数据为虚构，不含任何第三方产品规格或费率。
