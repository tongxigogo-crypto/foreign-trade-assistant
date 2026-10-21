/**
 * Product accessory (BOM) engine.
 *
 * The problem this solves: a customer orders one product, but shipping and
 * installing it needs a set of accessories. A salesperson who does not know the
 * product well forgets one — a bracket, a screw pack, a tube of sealant — and the
 * order goes out short.
 *
 * So this engine does not just multiply. It checks that every accessory declared
 * as required actually came out above zero, and it reports the ones that did not.
 *
 * No product data lives in this file. A product is described by a plain object
 * (see `data/product-master.example.js`).
 *
 * Constraints:
 *   - no DOM, so the engine runs under Node for verification;
 *   - no dependencies, no network;
 *   - works as a plain <script> (window.TradeEngine) and under Node
 *     (module.exports), because the delivered artefact is opened by double-click
 *     over file://;
 *   - rounding carries an epsilon guard so float noise cannot add a unit.
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

  /** Rounding tolerance. Absorbs float error before ceiling. */
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

  function isNonEmptyString(value) {
    return typeof value === 'string' && value.trim() !== '';
  }

  /**
   * Validate the input definitions.
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
      if (!isNonEmptyString(input.id)) {
        errors.push(label + '.id must be a non-empty string');
      } else if (seen[input.id]) {
        errors.push(label + '.id duplicates ' + input.id);
      } else {
        seen[input.id] = true;
      }
      if (!isNonEmptyString(input.label)) {
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
   * Validate a product definition.
   * @returns {{ valid: boolean, errors: string[], inputIds: string[] }}
   */
  function validateProduct(product) {
    var errors = [];
    if (!product || typeof product !== 'object') {
      return { valid: false, errors: ['product must be an object'], inputIds: [] };
    }
    if (!isNonEmptyString(product.id)) errors.push('product.id must be a non-empty string');
    if (!isNonEmptyString(product.name)) errors.push('product.name must be a non-empty string');

    var inputErrors = validateInputs(product.inputs);
    errors = errors.concat(inputErrors);
    var inputIds = Array.isArray(product.inputs)
      ? product.inputs.map(function (input) {
          return input && input.id;
        }).filter(isNonEmptyString)
      : [];
    var inputIdSet = {};
    inputIds.forEach(function (id) {
      inputIdSet[id] = true;
    });

    var accessories = product.accessories;
    if (!Array.isArray(accessories) || accessories.length === 0) {
      errors.push('product.accessories must be a non-empty array');
    } else {
      var seen = {};
      accessories.forEach(function (item, index) {
        var label = 'accessories[' + index + ']';
        if (!item || typeof item !== 'object') {
          errors.push(label + ' must be an object');
          return;
        }
        if (!isNonEmptyString(item.id)) {
          errors.push(label + '.id must be a non-empty string');
        } else if (seen[item.id]) {
          errors.push(label + '.id duplicates ' + item.id);
        } else {
          seen[item.id] = true;
        }
        if (!isNonEmptyString(item.label)) errors.push(label + '.label must be a non-empty string');

        var per = item.per;
        if (per !== undefined) {
          if (!per || typeof per !== 'object') {
            errors.push(label + '.per must be an object mapping input ids to factors');
          } else {
            Object.keys(per).forEach(function (key) {
              if (!inputIdSet[key]) {
                errors.push(label + '.per references unknown input "' + key + '"');
              }
              if (typeof per[key] !== 'number' || !Number.isFinite(per[key])) {
                errors.push(label + '.per.' + key + ' must be a finite number');
              }
            });
          }
        }
        if (item.fixed !== undefined && (typeof item.fixed !== 'number' || item.fixed < 0)) {
          errors.push(label + '.fixed must be a non-negative number when present');
        }
        if (per === undefined && item.fixed === undefined) {
          errors.push(label + ' declares neither per nor fixed, so it can never produce a quantity');
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

    return { valid: errors.length === 0, errors: errors, inputIds: inputIds };
  }

  /**
   * Coerce and range-check user input. Missing required values are reported,
   * never silently replaced with zero.
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
   * Compute one accessory line.
   *   raw = Σ(per[inputId] × values[inputId]) + fixed
   */
  function computeLine(item, values) {
    var total = item.fixed === undefined ? 0 : item.fixed;
    var sources = [];

    if (item.per) {
      Object.keys(item.per).forEach(function (key) {
        var contribution = item.per[key] * values[key];
        if (item.per[key] !== 0) {
          sources.push(key + ' × ' + item.per[key]);
        }
        total += contribution;
      });
    }
    if (item.fixed !== undefined && item.fixed !== 0) {
      sources.push('固定 ' + item.fixed);
    }

    return { raw: total, sources: sources };
  }

  /**
   * Run the accessory calculation.
   *
   * Returned `missing` is the point of this engine: every accessory marked
   * `required` whose quantity came out at zero.
   *
   * @param {object} product Validated product definition.
   * @param {object} raw Raw user input.
   * @param {{ applyOverage?: boolean }} [options]
   */
  function calculate(product, raw, options) {
    options = options || {};
    var applyOverage = options.applyOverage !== false;
    var failure = { ok: false, errors: [], warnings: [], lines: [], missing: [], groups: [] };

    var check = validateProduct(product);
    if (!check.valid) {
      failure.errors = check.errors;
      return failure;
    }

    var normalized = normalizeValues(product, raw);
    if (normalized.errors.length > 0) {
      failure.errors = normalized.errors;
      return failure;
    }

    var values = normalized.values;
    var lines = [];
    var warnings = [];
    var missing = [];
    var groupOrder = [];
    var groupTotals = {};

    product.accessories.forEach(function (item) {
      var computed;
      try {
        computed = computeLine(item, values);
      } catch (error) {
        warnings.push(item.label + ' 计算出错：' + (error && error.message ? error.message : String(error)));
        return;
      }

      if (!Number.isFinite(computed.raw)) {
        warnings.push(item.label + ' 算出了非有限值，请检查公式系数');
        return;
      }

      var rounding = item.rounding === undefined ? 'ceil' : item.rounding;
      var overage = item.overage === undefined ? 0 : item.overage;
      var withOverage = applyOverage ? computed.raw * (1 + overage) : computed.raw;
      var quantity = ROUNDING[rounding](withOverage);

      if (quantity < 0) {
        warnings.push(item.label + ' 算出了负数，请检查输入');
      }

      var group = item.group || '其他';
      if (!has(groupTotals, group)) {
        groupTotals[group] = { group: group, lines: 0 };
        groupOrder.push(group);
      }
      groupTotals[group].lines += 1;

      // The whole reason this engine exists.
      if (item.required === true && quantity === 0) {
        missing.push({
          id: item.id,
          label: item.label,
          unit: item.unit || '',
          reason: '必配项数量为 0',
        });
      }

      lines.push({
        id: item.id,
        label: item.label,
        group: group,
        unit: item.unit || '',
        required: item.required === true,
        raw: Number(computed.raw.toFixed(4)),
        quantity: quantity,
        rounding: rounding,
        overage: overage,
        sources: computed.sources,
        note: item.note,
      });
    });

    var groups = groupOrder.map(function (name) {
      return groupTotals[name];
    });

    return {
      ok: true,
      errors: [],
      warnings: warnings,
      lines: lines,
      missing: missing,
      groups: groups,
    };
  }

  /** Escape a value for CSV. */
  function csvCell(value) {
    var text = value === undefined || value === null ? '' : String(value);
    if (/[",\n\r]/.test(text)) {
      return '"' + text.replace(/"/g, '""') + '"';
    }
    return text;
  }

  /**
   * Build a CSV the salesperson can paste into a quotation sheet or hand to
   * production. Columns: 分组, 配件, 数量, 单位, 备注.
   *
   * @param {Array} lines Result lines from `calculate`.
   * @param {{ productName?: string, meta?: string }} [header]
   */
  function toCSV(lines, header) {
    header = header || {};
    var rows = [];
    if (header.productName) {
      rows.push([csvCell('产品'), csvCell(header.productName)].join(','));
    }
    if (header.meta) {
      rows.push([csvCell('说明'), csvCell(header.meta)].join(','));
    }
    if (rows.length > 0) rows.push('');

    rows.push(['分组', '配件', '数量', '单位', '备注'].map(csvCell).join(','));
    (lines || []).forEach(function (line) {
      rows.push(
        [line.group, line.label, line.quantity, line.unit, line.required ? '必配' : ''].map(csvCell).join(','),
      );
    });
    return rows.join('\r\n');
  }

  /**
   * Plain-text table for pasting into a chat window or a document.
   */
  function toPlainText(lines, header) {
    header = header || {};
    var out = [];
    if (header.productName) out.push(header.productName);
    if (header.meta) out.push(header.meta);
    if (out.length > 0) out.push('');

    (lines || []).forEach(function (line) {
      out.push(
        (line.group ? '[' + line.group + '] ' : '') +
          line.label +
          '：' +
          line.quantity +
          ' ' +
          (line.unit || ''),
      );
    });
    return out.join('\n');
  }

  return {
    EPSILON: EPSILON,
    ROUNDING: ROUNDING,
    validateInputs: validateInputs,
    validateProduct: validateProduct,
    normalizeValues: normalizeValues,
    calculate: calculate,
    toCSV: toCSV,
    toPlainText: toPlainText,
  };
});
