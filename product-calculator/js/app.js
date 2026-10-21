/**
 * UI controller. Contains no formulas — every number comes from the engine.
 */
(function () {
  'use strict';

  var engine = window.TradeEngine;
  var product = window.TradeProduct;
  var config = window.TradeConfig || {};

  var formEl = document.getElementById('input-form');
  var resultEl = document.getElementById('result');
  var messageEl = document.getElementById('message');
  var productNameEl = document.getElementById('product-name');
  var sourceTableEl = document.getElementById('source-table');
  var exportBarEl = document.getElementById('export-bar');

  var lastResult = null;

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

      var controlRow = el('div', 'control-row');
      controlRow.append(control);
      if (input.unit) controlRow.append(el('span', 'unit', input.unit));

      field.append(label, controlRow);
      if (input.hint) field.append(el('p', 'hint', input.hint));
      formEl.append(field);
    });

    var actions = el('div', 'actions');
    var submit = el('button', 'primary', '计算配件');
    submit.type = 'submit';
    var reset = el('button', 'ghost', '清空');
    reset.type = 'button';
    reset.addEventListener('click', function () {
      formEl.reset();
      resultEl.replaceChildren(el('p', 'placeholder', '填好左侧输入后点「计算配件」。'));
      exportBarEl.hidden = true;
      lastResult = null;
      showMessage('info', []);
    });
    actions.append(submit, reset);
    formEl.append(actions);
  }

  function renderSourceTable() {
    sourceTableEl.replaceChildren();

    var thead = el('thead');
    var head = el('tr');
    ['分组', '配件', '计算方式', '单位', '属性'].forEach(function (name) {
      head.append(el('th', null, name));
    });
    thead.append(head);
    sourceTableEl.append(thead);

    var tbody = el('tbody');
    product.accessories.forEach(function (item) {
      var row = el('tr');
      row.append(el('td', null, item.group || '其他'));
      row.append(el('td', null, item.label));

      var formula = [];
      Object.keys(item.per || {}).forEach(function (key) {
        var input = product.inputs.filter(function (candidate) {
          return candidate.id === key;
        })[0];
        formula.push((input ? input.label : key) + ' × ' + item.per[key]);
      });
      if (item.fixed) formula.push('固定 ' + item.fixed);

      row.append(el('td', 'note-cell', formula.join(' + ') || '—'));
      row.append(el('td', null, item.unit || '—'));
      row.append(el('td', null, item.required ? '必配' : '选配'));
      tbody.append(row);
    });
    sourceTableEl.append(tbody);
  }

  function renderMissing(missing) {
    if (!missing || missing.length === 0) return null;

    var box = el('div', 'missing-box');
    box.append(el('p', 'missing-title', '⚠ 有 ' + missing.length + ' 个必配配件算出来是 0'));
    box.append(
      el(
        'p',
        'missing-hint',
        '这些配件标了「必配」，但当前输入下数量为 0。要么补上数量，要么把它们改成选配——不能就这样交给客户。',
      ),
    );
    var list = el('ul');
    missing.forEach(function (item) {
      list.append(el('li', null, item.label + '（' + item.reason + '）'));
    });
    box.append(list);
    return box;
  }

  function renderResult(result) {
    resultEl.replaceChildren();
    exportBarEl.hidden = true;
    lastResult = null;

    if (!result.ok) {
      showMessage('error', result.errors);
      return;
    }

    showMessage(result.warnings.length ? 'warn' : 'info', result.warnings);

    var missingBox = renderMissing(result.missing);
    if (missingBox) resultEl.append(missingBox);

    var table = el('table', 'result-table');
    var thead = el('thead');
    var head = el('tr');
    ['配件', '数量', '单位', '计算值'].forEach(function (name) {
      head.append(el('th', null, name));
    });
    thead.append(head);
    table.append(thead);

    var tbody = el('tbody');
    var currentGroup = null;
    result.lines.forEach(function (line) {
      if (line.group !== currentGroup) {
        currentGroup = line.group;
        var groupRow = el('tr', 'group-row');
        var groupCell = el('td', null, line.group);
        groupCell.colSpan = 4;
        groupRow.append(groupCell);
        tbody.append(groupRow);
      }

      var tr = el('tr');
      var nameCell = el('td');
      nameCell.append(document.createTextNode(line.label));
      if (!line.required) nameCell.append(el('span', 'tag tag-optional', '选配'));
      tr.append(nameCell);

      var quantity = el('td', 'quantity', String(line.quantity));
      if (line.overage > 0) {
        quantity.append(el('span', 'badge', '+' + Math.round(line.overage * 100) + '%'));
      }
      tr.append(quantity);
      tr.append(el('td', null, line.unit || '—'));
      tr.append(el('td', 'raw', line.raw.toFixed(config.rawPrecision === undefined ? 2 : config.rawPrecision)));

      tbody.append(tr);
    });
    table.append(tbody);
    resultEl.append(table);

    var summary = el('p', 'summary');
    summary.textContent =
      '共 ' +
      result.lines.length +
      ' 项配件，分 ' +
      result.groups.length +
      ' 组：' +
      result.groups
        .map(function (group) {
          return group.group + ' ' + group.lines + ' 项';
        })
        .join('、');
    resultEl.append(summary);

    lastResult = result;
    exportBarEl.hidden = false;
  }

  function collectInput() {
    var raw = {};
    product.inputs.forEach(function (input) {
      var control = document.getElementById('input-' + input.id);
      raw[input.id] = control ? control.value : undefined;
    });
    return raw;
  }

  function headerText() {
    var parts = [];
    product.inputs.forEach(function (input) {
      var control = document.getElementById('input-' + input.id);
      if (control && control.value !== '') {
        parts.push(input.label + ' ' + control.value + (input.unit || ''));
      }
    });
    return parts.join('，');
  }

  function downloadCSV() {
    if (!lastResult) return;
    var csv = engine.toCSV(lastResult.lines, {
      productName: product.name,
      meta: headerText(),
    });
    // BOM keeps Excel from mangling UTF-8 Chinese.
    var blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
    var url = URL.createObjectURL(blob);
    var link = document.createElement('a');
    link.href = url;
    link.download = (product.id || 'bom') + '-配件清单.csv';
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(function () {
      URL.revokeObjectURL(url);
    }, 1000);
    showMessage('info', ['已导出 CSV。可粘贴进报价表或生产单。']);
  }

  function copyPlainText() {
    if (!lastResult) return;
    var text = engine.toPlainText(lastResult.lines, {
      productName: product.name,
      meta: headerText(),
    });

    var done = function () {
      showMessage('info', ['清单已复制，可直接粘贴到聊天窗口或文档。']);
    };
    var fallback = function () {
      var area = el('textarea');
      area.value = text;
      area.style.position = 'fixed';
      area.style.opacity = '0';
      document.body.append(area);
      area.select();
      try {
        document.execCommand('copy');
        done();
      } catch (error) {
        showMessage('error', ['复制失败，请手动选择清单文本。']);
      }
      area.remove();
    };

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done, fallback);
    } else {
      fallback();
    }
  }

  function boot() {
    if (!engine) {
      document.body.replaceChildren(el('p', 'fatal', '计算引擎未加载：请确认 js/engine.js 与本页面在同一目录。'));
      return;
    }
    if (!product) {
      document.body.replaceChildren(
        el('p', 'fatal', '产品数据未加载：请先复制 data/product-master.example.js 为 data/product-master.js，并在 index.html 中引用它。'),
      );
      return;
    }

    var check = engine.validateProduct(product);
    if (!check.valid) {
      document.body.replaceChildren(el('p', 'fatal', '产品数据格式有误：' + check.errors.join('；')));
      return;
    }

    document.title = config.title ? config.title + ' · ' + product.name : product.name;
    if (productNameEl) productNameEl.textContent = product.name;

    renderForm();
    renderSourceTable();

    if (/示例|demo|example/i.test(product.name)) {
      var banner = document.getElementById('demo-banner');
      if (banner) banner.hidden = false;
    }

    formEl.addEventListener('submit', function (event) {
      event.preventDefault();
      renderResult(engine.calculate(product, collectInput()));
    });

    document.getElementById('btn-csv').addEventListener('click', downloadCSV);
    document.getElementById('btn-copy').addEventListener('click', copyPlainText);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
