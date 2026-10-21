/**
 * EXAMPLE product definition — all numbers below are invented.
 *
 * Copy this file to `product-master.js` and replace the spec and the formulas
 * with your own. Nothing here represents a real product, a real supplier, or a
 * real price.
 *
 * A product definition has three parts:
 *   spec   — dimensions and constants the formulas read
 *   inputs — what the salesperson types in
 *   items  — what gets calculated, one line per material
 *
 * Each item's `compute(ctx)` receives:
 *   ctx.values  — validated numeric user input, keyed by input id
 *   ctx.spec    — this product's spec object
 *   ctx.ceil / ctx.floor / ctx.round — rounding helpers
 *   ctx.areaM2(widthMm, lengthMm)    — square metres from millimetre dimensions
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

  // One panel covers this much wall after the overlap is removed.
  var COVER_WIDTH_MM = 145;
  var PANEL_LENGTH_MM = 2900;
  var COVERAGE_PER_PANEL_M2 = (COVER_WIDTH_MM / 1000) * (PANEL_LENGTH_MM / 1000);

  return {
    id: 'demo-wall-panel',
    name: '示例墙板（虚构数据，仅演示格式）',
    specNote: 'Replace every number in this file with your own product data.',
    spec: {
      panelWidthMm: 159,
      panelLengthMm: PANEL_LENGTH_MM,
      coverWidthMm: COVER_WIDTH_MM,
      coveragePerPanelM2: COVERAGE_PER_PANEL_M2,
      clipsPerM2: 12,
      sealantM2PerTube: 8,
    },
    inputs: [
      {
        id: 'areaM2',
        label: '施工面积',
        unit: 'm²',
        min: 0.1,
        max: 100000,
        step: 0.1,
        placeholder: '例如 100',
      },
      {
        id: 'wastePercent',
        label: '损耗率',
        unit: '%',
        min: 0,
        max: 30,
        step: 0.5,
        required: false,
        default: 5,
      },
    ],
    items: [
      {
        id: 'panel',
        label: '主材板',
        unit: '块',
        rounding: 'ceil',
        note: '面积 ÷ 单板有效覆盖面积，含损耗率',
        compute: function (ctx) {
          var covered = ctx.values.areaM2 * (1 + ctx.values.wastePercent / 100);
          return covered / ctx.spec.coveragePerPanelM2;
        },
      },
      {
        id: 'clip',
        label: '固定卡扣',
        unit: '个',
        rounding: 'ceil',
        note: '面积 × 每平方米用量',
        compute: function (ctx) {
          return ctx.values.areaM2 * ctx.spec.clipsPerM2;
        },
      },
      {
        id: 'sealant',
        label: '密封胶',
        unit: '支',
        rounding: 'ceil',
        note: '面积 ÷ 每支可施工面积',
        compute: function (ctx) {
          return ctx.values.areaM2 / ctx.spec.sealantM2PerTube;
        },
      },
    ],
  };
});
