/**
 * Presentation settings. These are NOT calculation rules.
 * Anything that changes a number belongs in `product-master.js`.
 */
(function (root, factory) {
  var config = factory();
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = config;
  } else {
    root.TradeConfig = config;
  }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  return {
    title: '产品算料计算器',
    subtitle: '输入面积，得到主材与配件用量',
    /** Decimal places for the "raw" column. */
    rawPrecision: 2,
    /** Show the untruncated formula result next to the rounded quantity. */
    showRawValue: true,
    /** Warn when a line has a non-zero overage. */
    showOverageBadge: true,
  };
});
