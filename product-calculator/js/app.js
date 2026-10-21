/**
 * UI controller. Contains no formulas — every number comes from the engine.
 */
(function () {
  'use strict';

  var engine = window.TradeEngine;
  var product = window.TradeProduct;
  var config = window.TradeConfig || { title: '产品算料计算器', rawPrecision: 2 };

  var formEl = document.getElementById('input-form');
  var resultEl = document.getElementById('result');
  var messageEl = document.getElementById('message');
  var productNameEl = document.getElementById('product-name');
  var formulaEl = document.getElementById('formula-table');

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function showMessage(kind, lines) {
    messageEl.replaceChildren();
    if (!lines || lines.length === 0) {
      messageEl.hidden = true;
      return;
    }
    messageEl.hidden = false;
    messageEl.className = 'message message-' + kind;
    var list = el('ul');
    lines.forEach(function (line) {
      list.append(el('li', null, line));
    });
    messageEl.append(list);
  }

  function renderForm() {
    formEl.replaceChildren();

    product.inputs.forEach(function (input) {
      var field = el('div', 'field');
      var label = el('label', null, input.label);
      label.setAttribute('for', 'input-' + input.id);
      if (input.required === false) {
        label.append(el('span', 'optional', '选填'));
      }

      var control = el('input');
      control.id = 'input-' + input.id;
      control.name = input.id;
      control.type = 'number';
      control.inputMode = 'decimal';
      if (input.min !== undefined) control.min = String(input.min);
      if (input.max !== undefined) control.max = String(input.max);
      if (input.step !== undefined) control.step = String(input.step);
      if (input.placeholder) control.placeholder = input.placeholder;
      if (input.default !== undefined) control.value = String(input.default);

      var unit = null;
      if (input.unit) {
        unit = el('span', 'unit', input.unit);
      }

      var controlRow = el('div', 'control-row');
      controlRow.append(control);
      if (unit) controlRow.append(unit);

      field.append(label, controlRow);

      if (input.hint) {
        field.append(el('p', 'hint', input.hint));
      }

      formEl.append(field);
    });

    var actions = el('div', 'actions');
    var submit = el('button', 'primary', '计算用量');
    submit.type = 'submit';
    var reset = el('button', 'ghost', '清空');
    reset.type = 'button';
    reset.addEventListener('click', function () {
      formEl.reset();
      resultEl.replaceChildren();
      showMessage('info', []);
    });
    actions.append(submit, reset);
    formEl.append(actions);
  }

  function renderFormulaTable() {
    formulaEl.replaceChildren();
    var header = el('tr');
    ['项目', '单位', '取整', '说明'].forEach(function (name) {
      header.append(el('th', null, name));
    });
    var thead = el('thead');
    thead.append(header);
    formulaEl.append(thead);

    var tbody = el('tbody');
    product.items.forEach(function (item) {
      var row = el('tr');
      row.append(el('td', null, item.label));
      row.append(el('td', null, item.unit || '—'));
      row.append(el('td', null, item.rounding || 'ceil'));
      row.append(el('td', 'note-cell', item.note || '—'));
      tbody.append(row);
    });
    formulaEl.append(tbody);
  }

  function renderResult(result) {
    resultEl.replaceChildren();
    if (!result.ok) {
      showMessage('error', result.errors);
      return;
    }

    showMessage(result.warnings.length ? 'warn' : 'info', result.warnings);

    var table = el('table', 'result-table');
    var head = el('tr');
    ['项目', '用量', '单位', '计算值'].forEach(function (name) {
      head.append(el('th', null, name));
    });
    var thead = el('thead');
    thead.append(head);
    table.append(thead);

    var tbody = el('tbody');
    result.rows.forEach(function (row) {
      var tr = el('tr');
      tr.append(el('td', null, row.label));

      var quantity = el('td', 'quantity', String(row.quantity));
      if (row.overage > 0 && config.showOverageBadge !== false) {
        quantity.append(el('span', 'badge', '+' + Math.round(row.overage * 100) + '% 损耗'));
      }
      tr.append(quantity);

      tr.append(el('td', null, row.unit || '—'));

      var raw = el('td', 'raw');
      raw.textContent =
        config.showRawValue === false
          ? '—'
          : row.raw.toFixed(config.rawPrecision === undefined ? 2 : config.rawPrecision);
      tr.append(raw);

      tbody.append(tr);
    });
    table.append(tbody);
    resultEl.append(table);

    var units = Object.keys(result.summary.valueByUnit);
    if (units.length > 0) {
      var summary = el('p', 'summary');
      summary.textContent =
        '共 ' +
        result.summary.lineCount +
        ' 项：' +
        units
          .map(function (unit) {
            return result.summary.valueByUnit[unit] + ' ' + (unit || '件');
          })
          .join('、');
      resultEl.append(summary);
    }
  }

  function onSubmit(event) {
    event.preventDefault();
    var raw = {};
    product.inputs.forEach(function (input) {
      var control = document.getElementById('input-' + input.id);
      raw[input.id] = control ? control.value : undefined;
    });
    renderResult(engine.calculate(product, raw));
  }

  function boot() {
    if (!engine) {
      document.body.replaceChildren(
        el('p', 'fatal', '计算引擎未加载：请确认 js/engine.js 与本页面在同一目录。'),
      );
      return;
    }
    if (!product) {
      document.body.replaceChildren(
        el('p', 'fatal', '产品数据未加载：请确认 data/product-master.js 存在，或先复制 data/product-master.example.js。'),
      );
      return;
    }

    var check = engine.validateProduct(product);
    if (!check.valid) {
      document.body.replaceChildren(el('p', 'fatal', '产品数据格式有误：' + check.errors.join('；')));
      return;
    }

    document.title = config.title || product.name;
    if (productNameEl) productNameEl.textContent = product.name;

    renderForm();
    renderFormulaTable();

    if (/示例|demo|example/i.test(product.name)) {
      var banner = document.getElementById('demo-banner');
      if (banner) banner.hidden = false;
    }

    formEl.addEventListener('submit', onSubmit);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
