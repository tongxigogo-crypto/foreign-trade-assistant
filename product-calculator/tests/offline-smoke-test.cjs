/**
 * Offline engine verification. Runs under plain Node, no dependencies.
 *
 *   node tests/offline-smoke-test.cjs
 *
 * This checks numbers, not pixels. Browser acceptance is separate.
 */
'use strict';

const path = require('node:path');
const assert = require('node:assert');

const enginePath = path.join(__dirname, '..', 'js', 'engine.js');
const productPath = path.join(__dirname, '..', 'data', 'product-master.example.js');

const engine = require(enginePath);
const product = require(productPath);

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

console.log('\nengine smoke test\n');

check('the example product definition is valid', () => {
  const result = engine.validateProduct(product);
  assert.equal(result.valid, true, result.errors.join('; '));
});

check('100 m2 at 5% waste produces the expected quantities', () => {
  const result = engine.calculate(product, { areaM2: 100, wastePercent: 5 });
  assert.equal(result.ok, true, result.errors.join('; '));

  const byId = Object.fromEntries(result.rows.map((row) => [row.id, row]));

  // 100 * 1.05 / (0.145 * 2.9) = 249.70 -> 250
  assert.equal(byId.panel.quantity, 250, 'panel quantity');
  assert.equal(byId.clip.quantity, 1200, 'clip quantity');
  // 100 / 8 = 12.5 -> 13
  assert.equal(byId.sealant.quantity, 13, 'sealant quantity');
});

check('zero waste gives a smaller panel count', () => {
  const withWaste = engine.calculate(product, { areaM2: 100, wastePercent: 5 });
  const withoutWaste = engine.calculate(product, { areaM2: 100, wastePercent: 0 });
  const a = withWaste.rows.find((row) => row.id === 'panel').quantity;
  const b = withoutWaste.rows.find((row) => row.id === 'panel').quantity;
  assert.ok(b < a, 'panel count without waste should be lower: ' + b + ' vs ' + a);
  assert.equal(b, 238, '100 / 0.4205 = 237.81 -> 238');
});

check('a missing required input is reported, not silently zeroed', () => {
  const result = engine.calculate(product, {});
  assert.equal(result.ok, false);
  assert.ok(
    result.errors.some((message) => message.includes('施工面积')),
    'expected an error naming the missing input, got: ' + result.errors.join('; '),
  );
});

check('a non-numeric input is rejected', () => {
  const result = engine.calculate(product, { areaM2: 'abc' });
  assert.equal(result.ok, false);
  assert.ok(result.errors.some((message) => message.includes('must be a number')));
});

check('an out-of-range input is rejected', () => {
  const result = engine.calculate(product, { areaM2: 100, wastePercent: 99 });
  assert.equal(result.ok, false);
  assert.ok(result.errors.some((message) => message.includes('at most 30')));
});

check('float noise does not push a whole number up', () => {
  const tiny = {
    id: 'epsilon',
    name: 'epsilon',
    inputs: [{ id: 'n', label: 'n', min: 0 }],
    items: [
      {
        id: 'line',
        label: 'line',
        unit: '件',
        rounding: 'ceil',
        // 10.0000000001 must round to 10, not 11.
        compute: () => 10.0000000001,
      },
    ],
  };
  const result = engine.calculate(tiny, { n: 1 });
  assert.equal(result.ok, true, result.errors.join('; '));
  assert.equal(result.rows[0].quantity, 10);
});

check('an invalid product definition is rejected with reasons', () => {
  const broken = { id: 'x', name: 'x', inputs: [], items: [] };
  const result = engine.validateProduct(broken);
  assert.equal(result.valid, false);
  assert.ok(result.errors.length >= 2);
});

check('a throwing formula becomes a warning, not a crash', () => {
  const risky = {
    id: 'risky',
    name: 'risky',
    inputs: [{ id: 'n', label: 'n' }],
    items: [
      {
        id: 'boom',
        label: '会出错的行',
        unit: '件',
        compute: () => {
          throw new Error('formula failure');
        },
      },
    ],
  };
  const result = engine.calculate(risky, { n: 1 });
  assert.equal(result.ok, true);
  assert.equal(result.rows.length, 0);
  assert.match(result.warnings[0], /formula failure/);
});

check('unit totals aggregate per unit', () => {
  const result = engine.calculate(product, { areaM2: 10, wastePercent: 0 });
  assert.equal(result.summary.valueByUnit['块'], result.rows.find((r) => r.id === 'panel').quantity);
  assert.equal(result.summary.valueByUnit['个'], 120);
});

console.log('\n' + passed + ' passed, ' + failures.length + ' failed\n');

if (failures.length > 0) {
  failures.forEach((failure) => console.error('FAILED: ' + failure.name + ' — ' + failure.message));
  process.exit(1);
}
