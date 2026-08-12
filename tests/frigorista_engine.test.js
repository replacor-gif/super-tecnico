'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const engine = require('../assets/frigorista-engine.js');

const root = path.resolve(__dirname, '..');
const catalog = JSON.parse(fs.readFileSync(path.join(root, 'data/frigorista/catalog.json'), 'utf8'));
const curves = JSON.parse(fs.readFileSync(path.join(root, 'data/frigorista/pt-curves.json'), 'utf8'));

assert.equal(catalog.counts.pt_available, 56);
assert.equal(Object.keys(curves.curves).length, 56);

assert.equal(engine.toAbsolutePressurePa(0, 'bar', 'gauge'), 101325);
assert.ok(Math.abs(engine.toAbsolutePressurePa(100, 'psi', 'absolute') - 689475.7293168) < 0.001);

const r32 = engine.convertPressureToTemperature({
  catalog,
  curves,
  designation: 'r-32',
  pressure: 0,
  unit: 'bar',
  reference: 'gauge',
});
assert.equal(r32.designation, 'R32');
assert.equal(r32.result_type, 'single');
assert.ok(r32.saturation_temperature_c > -53 && r32.saturation_temperature_c < -51);

const r407c = engine.convertPressureToTemperature({
  catalog,
  curves,
  designation: 'R407C',
  pressure: 5,
  unit: 'bar',
  reference: 'gauge',
});
assert.equal(r407c.result_type, 'bubble_dew');
assert.ok(r407c.dew_temperature_c > r407c.bubble_temperature_c);
assert.ok(r407c.glide_k > 3);

const superheat = engine.calculateSuperheat(4.2, 11.7);
assert.equal(superheat.value_k, 7.5);
const subcooling = engine.calculateSubcooling(42.5, 36.2);
assert.equal(subcooling.value_k, 6.3);

assert.equal(engine.nextUsefulMeasurement({measurements: {}}).code, 'low_pressure');
assert.equal(engine.nextUsefulMeasurement({measurements: {
  low_pressure: {},
  suction_line_temperature: {},
  high_pressure: {},
  liquid_line_temperature: {},
}}).code, 'return_air_temperature');

assert.throws(
  () => engine.convertPressureToTemperature({catalog, curves, designation: 'R744', pressure: 10}),
  error => error.code === 'unsupported_refrigerant'
);
assert.throws(
  () => engine.convertPressureToTemperature({catalog, curves, designation: 'R513B', pressure: 5}),
  error => error.code === 'unsupported_refrigerant'
);

console.log('Frigorista engine tests: OK');
