/**
 * Generic material take-off engine.
 *
 * This file contains no product data and no business rules. A product is
 * described by a plain object (see `data/product-master.example.js`) and this
 * engine turns that description plus user input into a quantity list.
 *
 * Design constraints:
 *   - no DOM access, so the engine can run under Node for verification;
 *   - no network access, no dependencies;
 *   - works both as a plain <script> (window.TradeEngine) and under Node
 *     (module.exports), because the delivered artefact is opened by
 *     double-clicking index.html over file://;
 *   - rounding is explicit per line item, with an epsilon guard so that
 *     `10.0000000001` does not round up to 11.
 */
(function (root, factory) {
  var api = factory();
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  } else {
    root.TradeEngine = api;
  }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  /** Rounding tolerance. Absorbs float error from division before ceiling. */
  var EPSILON = 1e-9;

  var ROUNDING = {
    ceil: function (value) {
      return Math.ceil(value - EPSILON);
    },
    floor: function (value) {
      return Math.floor(value + EPSILON);
    },
    round: function (value) {
      return Math.round(value);
    },
    none: function (value) {
      return value;
    },
  };

  function has(object, key) {
    return Object.prototype.hasOwnProperty.call(object, key);
  }

  /**
   * Validate an input definition list from a product object.
   * @returns {string[]} error messages, empty when valid
   */
  function validateInputs(inputs) {
    var errors = [];
    if (!Array.isArray(inputs) || inputs.length === 0) {
      return ['product.inputs must be a non-empty array'];
    }
    var seen = {};
    inputs.forEach(function (input, index) {
      var label = 'inputs[' + index + ']';
      if (!input || typeof input !== 'object') {
        errors.push(label + ' must be an object');
        return;
      }
      if (typeof input.id !== 'string' || input.id.trim() === '') {
        errors.push(label + '.id must be a non-empty string');
      } else if (seen[input.id]) {
        errors.push(label + '.id duplicates ' + input.id);
      } else {
        seen[input.id] = true;
      }
      if (typeof input.label !== 'string' || input.label.trim() === '') {
        errors.push(label + '.label must be a non-empty string');
      }
      if (input.min !== undefined && typeof input.min !== 'number') {
        errors.push(label + '.min must be a number when present');
      }
      if (input.max !== undefined && typeof input.max !== 'number') {
        errors.push(label + '.max must be a number when present');
      }
      if (input.min !== undefined && input.max !== undefined && input.min > input.max) {
        errors.push(label + ' has min greater than max');
      }
    });
    return errors;
  }

  /**
   * Validate a product definition before it is used.
   * @returns {{ valid: boolean, errors: string[] }}
   */
  function validateProduct(product) {
    var errors = [];
    if (!product || typeof product !== 'object') {
      return { valid: false, errors: ['product must be an object'] };
    }
    if (typeof product.id !== 'string' || product.id.trim() === '') {
      errors.push('product.id must be a non-empty string');
    }
    if (typeof product.name !== 'string' || product.name.trim() === '') {
      errors.push('product.name must be a non-empty string');
    }
    errors = errors.concat(validateInputs(product.inputs));

    if (!Array.isArray(product.items) || product.items.length === 0) {
      errors.push('product.items must be a non-empty array');
    } else {
      var seen = {};
      product.items.forEach(function (item, index) {
        var label = 'items[' + index + ']';
        if (!item || typeof item !== 'object') {
          errors.push(label + ' must be an object');
          return;
        }
        if (typeof item.id !== 'string' || item.id.trim() === '') {
          errors.push(label + '.id must be a non-empty string');
        } else if (seen[item.id]) {
          errors.push(label + '.id duplicates ' + item.id);
        } else {
          seen[item.id] = true;
        }
        if (typeof item.label !== 'string' || item.label.trim() === '') {
          errors.push(label + '.label must be a non-empty string');
        }
        if (typeof item.compute !== 'function') {
          errors.push(label + '.compute must be a function');
        }
        var rounding = item.rounding === undefined ? 'ceil' : item.rounding;
        if (!has(ROUNDING, rounding)) {
          errors.push(label + '.rounding must be one of ' + Object.keys(ROUNDING).join(', '));
        }
        if (item.overage !== undefined && (typeof item.overage !== 'number' || item.overage < 0)) {
          errors.push(label + '.overage must be a non-negative number when present');
        }
      });
    }

    return { valid: errors.length === 0, errors: errors };
  }

  /**
   * Coerce and range-check user input against the product's input definitions.
   * Missing or empty values are reported, never silently zeroed.
   * @returns {{ values: Object, errors: string[] }}
   */
  function normalizeValues(product, raw) {
    raw = raw || {};
    var values = {};
    var errors = [];
    var inputs = product.inputs || [];

    for (var i = 0; i < inputs.length; i += 1) {
      var input = inputs[i];
      var source = raw[input.id];
      var isEmpty = source === undefined || source === null || String(source).trim() === '';

      if (isEmpty) {
        if (input.required === false) {
          values[input.id] = input.default === undefined ? 0 : input.default;
          continue;
        }
        errors.push(input.label + ' is required');
        values[input.id] = Number.NaN;
        continue;
      }

      var numeric = Number(source);
      if (!Number.isFinite(numeric)) {
        errors.push(input.label + ' must be a number');
        values[input.id] = Number.NaN;
        continue;
      }
      if (input.min !== undefined && numeric < input.min) {
        errors.push(input.label + ' must be at least ' + input.min);
      }
      if (input.max !== undefined && numeric > input.max) {
        errors.push(input.label + ' must be at most ' + input.max);
      }
      values[input.id] = numeric;
    }

    return { values: values, errors: errors };
  }

  /**
   * Run a product's take-off.
   *
   * @param {object} product Validated product definition.
   * @param {object} raw Raw user input.
   * @param {{ applyOverage?: boolean }} [options]
   */
  function calculate(product, raw, options) {
    options = options || {};
    var applyOverage = options.applyOverage !== false;
    var empty = { ok: false, errors: [], warnings: [], rows: [], summary: { lineCount: 0, valueByUnit: {} } };

    var check = validateProduct(product);
    if (!check.valid) {
      empty.errors = check.errors;
      return empty;
    }

    var normalized = normalizeValues(product, raw);
    if (normalized.errors.length > 0) {
      empty.errors = normalized.errors;
      return empty;
    }

    var values = normalized.values;
    var spec = product.spec || {};
    var ctx = {
      values: values,
      spec: spec,
      ceil: ROUNDING.ceil,
      floor: ROUNDING.floor,
      round: ROUNDING.round,
      /** Square metres from millimetre dimensions. */
      areaM2: function (widthMm, lengthMm) {
        return (widthMm * lengthMm) / 1000000;
      },
    };

    var rows = [];
    var warnings = [];
    var valueByUnit = {};

    product.items.forEach(function (item) {
      var rawValue;
      try {
        rawValue = item.compute(ctx);
      } catch (error) {
        warnings.push(item.label + ' failed to compute: ' + (error && error.message ? error.message : String(error)));
        return;
      }

      if (!Number.isFinite(rawValue)) {
        warnings.push(item.label + ' produced a non-finite value; check the formula');
        return;
      }

      var rounding = item.rounding === undefined ? 'ceil' : item.rounding;
      var overage = item.overage === undefined ? 0 : item.overage;
      var withOverage = applyOverage ? rawValue * (1 + overage) : rawValue;
      var quantity = ROUNDING[rounding](withOverage);

      if (quantity < 0) {
        warnings.push(item.label + ' produced a negative quantity; check the input signs');
      }

      var unit = item.unit || '';
      valueByUnit[unit] = (valueByUnit[unit] || 0) + quantity;

      rows.push({
        id: item.id,
        label: item.label,
        unit: unit,
        raw: Number(rawValue.toFixed(4)),
        quantity: quantity,
        rounding: rounding,
        overage: overage,
        note: item.note,
      });
    });

    return {
      ok: true,
      errors: [],
      warnings: warnings,
      rows: rows,
      summary: { lineCount: rows.length, valueByUnit: valueByUnit },
    };
  }

  return {
    EPSILON: EPSILON,
    ROUNDING: ROUNDING,
    validateInputs: validateInputs,
    validateProduct: validateProduct,
    normalizeValues: normalizeValues,
    calculate: calculate,
  };
});
