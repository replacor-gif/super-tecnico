'use strict';

const assert = require('node:assert/strict');
const engine = require('../assets/condensate-drain-engine.js');

assert.ok(Math.abs(engine.capacityToKw(3000, 'frig_h') - 3.489) < 0.001);
assert.ok(Math.abs(engine.capacityToKw(12000, 'btu_h') - 3.51685284) < 0.00001);
assert.equal(engine.capacityToKw(4.2, 'kw'), 4.2);

const normal = engine.estimateCondensateLh(5, 'kw', 'normal');
const humid = engine.estimateCondensateLh(5, 'kw', 'humid');
const veryHumid = engine.estimateCondensateLh(5, 'kw', 'very_humid');
assert.ok(normal < humid && humid < veryHumid);

const result = engine.designNetwork({
  slope_percent: 1,
  units: [
    { name: 'Dormitorio', mode: 'known_flow', flow_l_h: 2, connection_mm: 16, segment_length_m: 4 },
    { name: 'Salón', mode: 'known_flow', flow_l_h: 4, connection_mm: 20, segment_length_m: 7 },
  ],
});
assert.equal(result.segments.length, 2);
assert.equal(result.segments[0].cumulative_raw_flow_l_h, 2);
assert.equal(result.segments[1].cumulative_raw_flow_l_h, 6);
assert.ok(result.segments[0].recommended_internal_diameter_mm >= 16);
assert.ok(result.segments[1].recommended_internal_diameter_mm >= 20);
assert.equal(result.segments[0].fall_cm, 4);
assert.equal(result.total_fall_cm, 11);
assert.equal(result.collector_internal_diameter_mm, result.segments[1].recommended_internal_diameter_mm);

const estimated = engine.designNetwork({
  slope_percent: 0.5,
  units: [{ name: 'Cassette', mode: 'capacity', capacity: 10000, capacity_unit: 'frig_h', climate: 'very_humid', connection_mm: 25, segment_length_m: 9 }],
});
assert.equal(estimated.collector_internal_diameter_mm >= 25, true);
assert.equal(estimated.warnings.some(item => item.includes('estimados')), true);
assert.equal(estimated.warnings.some(item => item.includes('Pendiente')), true);

assert.throws(() => engine.designNetwork({ units: [] }), /al menos un equipo/);
assert.throws(() => engine.designNetwork({ slope_percent: 0, units: [{ mode: 'known_flow', flow_l_h: 2 }] }), /pendiente/);
assert.throws(() => engine.capacityToKw(-1, 'kw'), /igual o mayor que cero/);

console.log('Condensate drain engine tests: OK');
