/**
 * EXAMPLE product definition — every number below is invented.
 *
 * Copy this file to `product-master.js` and replace the parts and factors with
 * your own. Nothing here represents a real product, a real supplier, or a real
 * price.
 *
 * A product definition has three parts:
 *   inputs      — what the salesperson types in (order quantity, dimensions)
 *   accessories — the parts that must ship with it
 *   groups      — how the accessory rows are grouped in the output
 *
 * Each accessory's quantity is:
 *   Σ (per[inputId] × inputValue) + fixed
 * then multiplied by (1 + overage) and rounded.
 *
 * `required: true` is the important field. If a required accessory computes to
 * zero, the result reports it as a missing part instead of quietly shipping an
 * incomplete set.
 */
(function (root, factory) {
  var product = factory();
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = product;
  } else {
    root.TradeProduct = product;
  }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  return {
    id: 'demo-sliding-door',
    name: '示例推拉门套件（虚构数据，仅演示格式）',
    unitLabel: '套',
    specNote: 'Replace every number and label in this file with your own product data.',
    inputs: [
      {
        id: 'quantity',
        label: '订购数量',
        unit: '套',
        min: 1,
        max: 100000,
        step: 1,
        default: 1,
        placeholder: '例如 10',
      },
      {
        id: 'widthM',
        label: '单套宽度',
        unit: 'm',
        min: 0.3,
        max: 6,
        step: 0.05,
        required: false,
        default: 1.2,
        hint: '影响导轨、密封条这类按米计算的配件',
      },
    ],
    accessories: [
      // —— 主体 ——
      {
        id: 'frame',
        label: '门框',
        unit: '件',
        group: '主体',
        required: true,
        per: { quantity: 1 },
        note: '每套一件',
      },
      {
        id: 'door-leaf',
        label: '门扇',
        unit: '件',
        group: '主体',
        required: true,
        per: { quantity: 1 },
      },
      {
        id: 'track',
        label: '导轨',
        unit: '米',
        group: '主体',
        required: true,
        per: { quantity: 1, widthM: 1 },
        note: '每套按宽度取米数',
      },

      // —— 五金 ——
      {
        id: 'roller-top',
        label: '上滑轮',
        unit: '个',
        group: '五金',
        required: true,
        per: { quantity: 2 },
      },
      {
        id: 'roller-bottom',
        label: '下滑轮',
        unit: '个',
        group: '五金',
        required: true,
        per: { quantity: 2 },
      },
      {
        id: 'handle',
        label: '拉手',
        unit: '个',
        group: '五金',
        required: true,
        per: { quantity: 1 },
      },
      {
        id: 'screw-pack',
        label: '安装螺丝包',
        unit: '包',
        group: '五金',
        required: true,
        per: { quantity: 1 },
        overage: 0.05,
        note: '含 5% 备损',
      },

      // —— 辅料 ——
      {
        id: 'seal-strip',
        label: '密封条',
        unit: '米',
        group: '辅料',
        required: true,
        per: { widthM: 2 },
        note: '两侧各一条',
      },
      {
        id: 'sealant',
        label: '密封胶',
        unit: '支',
        group: '辅料',
        required: false,
        per: { quantity: 0.5 },
        note: '每两套一支，选配',
      },
      {
        id: 'carton',
        label: '包装箱',
        unit: '个',
        group: '辅料',
        required: true,
        per: { quantity: 1 },
      },
      {
        id: 'manual',
        label: '安装说明书',
        unit: '份',
        group: '辅料',
        required: false,
        fixed: 1,
        note: '每个订单一份，与数量无关',
      },
    ],
  };
});
