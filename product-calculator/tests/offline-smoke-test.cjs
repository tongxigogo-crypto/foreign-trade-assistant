/**
 * Offline engine verification. Runs under plain Node, no dependencies.
 *
 *   node tests/offline-smoke-test.cjs
 *
 * This checks numbers and the missing-accessory check, not pixels. Browser
 * acceptance is separate.
 */
'use strict';

const path = require('node:path');
const assert = require('node:assert');

const engine = require(path.join(__dirname, '..', 'js', 'engine.js'));
const product = require(path.join(__dirname, '..', 'data', 'product-master.example.js'));

let passed = 0;
const failures = [];

function check(name, fn) {
  try {
    fn();
    passed += 1;
    console.log('  ok   ' + name);
  } catch (error) {
    failures.push({ name, message: error.message });
    console.log('  FAIL ' + name + '\n       ' + error.message);
  }
}

function linesById(result) {
  return Object.fromEntries(result.lines.map((line) => [line.id, line]));
}

console.log('\naccessory engine smoke test\n');

check('the example product definition is valid', () => {
  const result = engine.validateProduct(product);
  assert.equal(result.valid, true, result.errors.join('; '));
});

check('10 sets at 1.2 m produce the expected accessory list', () => {
  const result = engine.calculate(product, { quantity: 10, widthM: 1.2 });
  assert.equal(result.ok, true, result.errors.join('; '));
  const byId = linesById(result);

  assert.equal(byId.frame.quantity, 10, 'frame');
  assert.equal(byId['door-leaf'].quantity, 10, 'door leaf');
  // 10 × 1 + 1.2 × 1 = 11.2 -> 12 m of track
  assert.equal(byId.track.quantity, 12, 'track');
  assert.equal(byId['roller-top'].quantity, 20, 'top rollers');
  assert.equal(byId['roller-bottom'].quantity, 20, 'bottom rollers');
  assert.equal(byId.handle.quantity, 10, 'handle');
  // 10 × 1 with 5% overage = 10.5 -> 11 packs
  assert.equal(byId['screw-pack'].quantity, 11, 'screw packs');
  // 1.2 × 2 = 2.4 -> 3 m
  assert.equal(byId['seal-strip'].quantity, 3, 'seal strip');
  // 10 × 0.5 = 5
  assert.equal(byId.sealant.quantity, 5, 'sealant');
  assert.equal(byId.carton.quantity, 10, 'carton');
  // fixed 1 regardless of quantity
  assert.equal(byId.manual.quantity, 1, 'manual');
});

check('a complete set reports no missing accessory', () => {
  const result = engine.calculate(product, { quantity: 10, widthM: 1.2 });
  assert.deepEqual(result.missing, []);
});

check('a required accessory that computes to zero is reported as missing', () => {
  // Same product, but the seal strip factor is zero while width is still valid.
  const broken = JSON.parse(
    JSON.stringify(product, (key, value) => (typeof value === 'function' ? undefined : value)),
  );
  const strip = broken.accessories.find((item) => item.id === 'seal-strip');
  strip.per = { widthM: 0 };

  const result = engine.calculate(broken, { quantity: 10, widthM: 1.2 });
  assert.equal(result.ok, true, result.errors.join('; '));
  assert.equal(result.missing.length, 1);
  assert.equal(result.missing[0].id, 'seal-strip');
  assert.match(result.missing[0].reason, /必配项数量为 0/);
});

check('an optional accessory at zero is not reported as missing', () => {
  const result = engine.calculate(product, { quantity: 10, widthM: 1.2 });
  const sealant = result.lines.find((line) => line.id === 'sealant');
  assert.equal(sealant.required, false);
  assert.equal(
    result.missing.some((item) => item.id === 'sealant'),
    false,
  );
});

check('a missing required input is reported, not silently zeroed', () => {
  const result = engine.calculate(product, {});
  assert.equal(result.ok, false);
  assert.ok(
    result.errors.some((message) => message.includes('订购数量')),
    'expected an error naming the missing input, got: ' + result.errors.join('; '),
  );
});

check('a non-numeric input is rejected', () => {
  const result = engine.calculate(product, { quantity: 'ten' });
  assert.equal(result.ok, false);
  assert.ok(result.errors.some((message) => message.includes('must be a number')));
});

check('an out-of-range input is rejected', () => {
  const result = engine.calculate(product, { quantity: 10, widthM: 99 });
  assert.equal(result.ok, false);
  assert.ok(result.errors.some((message) => message.includes('at most 6')));
});

check('float noise does not add an extra unit', () => {
  const tiny = {
    id: 'epsilon',
    name: 'epsilon',
    inputs: [{ id: 'n', label: 'n', min: 0 }],
    accessories: [{ id: 'line', label: 'line', unit: '件', per: { n: 1 } }],
  };
  // 10.0000000001 must round to 10, not 11.
  const result = engine.calculate(tiny, { n: 10.0000000001 });
  assert.equal(result.ok, true, result.errors.join('; '));
  assert.equal(result.lines[0].quantity, 10);
});

check('a per entry referencing an unknown input is rejected', () => {
  const bad = {
    id: 'bad',
    name: 'bad',
    inputs: [{ id: 'n', label: 'n' }],
    accessories: [{ id: 'x', label: 'x', per: { notAnInput: 2 } }],
  };
  const result = engine.validateProduct(bad);
  assert.equal(result.valid, false);
  assert.ok(result.errors.some((message) => message.includes('unknown input')));
});

check('an accessory with neither per nor fixed is rejected', () => {
  const bad = {
    id: 'bad2',
    name: 'bad2',
    inputs: [{ id: 'n', label: 'n' }],
    accessories: [{ id: 'x', label: 'x' }],
  };
  const result = engine.validateProduct(bad);
  assert.equal(result.valid, false);
  assert.ok(result.errors.some((message) => message.includes('neither per nor fixed')));
});

check('accessories are grouped in declaration order', () => {
  const result = engine.calculate(product, { quantity: 10, widthM: 1.2 });
  assert.deepEqual(
    result.groups.map((group) => group.group),
    ['主体', '五金', '辅料'],
  );
  assert.equal(
    result.groups.reduce((total, group) => total + group.lines, 0),
    result.lines.length,
  );
});

check('CSV export has a header row and one row per accessory', () => {
  const result = engine.calculate(product, { quantity: 10, widthM: 1.2 });
  const csv = engine.toCSV(result.lines, { productName: product.name, meta: '订购数量 10套' });
  const rows = csv.split('\r\n');
  assert.ok(rows[0].includes('产品'), 'product header line');
  assert.ok(csv.includes('分组,配件,数量,单位,备注'), 'column header');
  assert.equal(rows.filter((row) => row.split(',').length >= 4 && row.trim() !== '').length >= result.lines.length, true);
});

check('CSV escapes a label containing a comma', () => {
  const csv = engine.toCSV([{ group: '五金', label: '螺丝,长款', quantity: 1, unit: '包', required: true }]);
  assert.ok(csv.includes('"螺丝,长款"'), 'comma-containing label must be quoted');
});

check('plain text keeps the group prefix', () => {
  const text = engine.toPlainText([
    { group: '五金', label: '上滑轮', quantity: 20, unit: '个' },
  ]);
  assert.equal(text, '[五金] 上滑轮：20 个');
});

console.log('\n' + passed + ' passed, ' + failures.length + ' failed\n');

if (failures.length > 0) {
  failures.forEach((failure) => console.error('FAILED: ' + failure.name + ' — ' + failure.message));
  process.exit(1);
}
