'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const engine = require('../assets/frigorista-engine.js');

const root = path.resolve(__dirname, '..');
const catalog = JSON.parse(fs.readFileSync(path.join(root, 'data/frigorista/catalog.json'), 'utf8'));
const curves = JSON.parse(fs.readFileSync(path.join(root, 'data/frigorista/pt-curves.json'), 'utf8'));
const mollier = JSON.parse(fs.readFileSync(path.join(root, 'data/frigorista/mollier-data.json'), 'utf8'));

assert.equal(catalog.counts.pt_available, 56);
assert.equal(Object.keys(curves.curves).length, 56);
assert.equal(Object.keys(mollier.refrigerants).length, 56);
assert.equal(mollier.dataset_version, catalog.dataset_version);

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
}}).code, 'discharge_line_temperature');
assert.equal(engine.nextUsefulMeasurement({measurements: {
  low_pressure: {},
  suction_line_temperature: {},
  high_pressure: {},
  liquid_line_temperature: {},
  discharge_line_temperature: {},
}}).code, 'return_air_temperature');

const r32Low = engine.convertPressureToTemperature({
  catalog, curves, designation: 'R32', pressure: 7, unit: 'bar', reference: 'gauge',
});
const r32High = engine.convertPressureToTemperature({
  catalog, curves, designation: 'R32', pressure: 20, unit: 'bar', reference: 'gauge',
});
const mollierMeasurements = {
  low_pressure: {input: {value: 7, unit: 'bar', reference: 'gauge'}, result: r32Low},
  suction_line_temperature: {value: 15, unit: 'degC', quality: 'measured'},
  high_pressure: {input: {value: 20, unit: 'bar', reference: 'gauge'}, result: r32High},
  liquid_line_temperature: {value: 30, unit: 'degC', quality: 'measured'},
};
const partialCycle = engine.analyzeMollierCycle({mollier, designation: 'R32', measurements: mollierMeasurements});
assert.equal(partialCycle.status, 'partial');
assert.ok(partialCycle.points.suction.enthalpy_kj_kg > partialCycle.points.liquid.enthalpy_kj_kg);
assert.equal(partialCycle.points.expansion.enthalpy_kj_kg, partialCycle.points.liquid.enthalpy_kj_kg);
assert.ok(partialCycle.performance.evaporator_effect_kj_kg > 0);
assert.equal(partialCycle.performance.cop_cycle, undefined);
const partialPlot = engine.createMollierPlotModel(mollier, partialCycle);
assert.ok(partialPlot.bubble.length >= 4);
assert.equal(Object.keys(partialPlot.points).length, 3);

const completeCycle = engine.analyzeMollierCycle({
  mollier,
  designation: 'R32',
  measurements: {
    ...mollierMeasurements,
    discharge_line_temperature: {value: 85, unit: 'degC', quality: 'measured'},
  },
});
assert.equal(completeCycle.status, 'complete');
assert.ok(completeCycle.performance.compressor_work_kj_kg > 0);
assert.ok(completeCycle.performance.condenser_heat_kj_kg > 0);
assert.ok(completeCycle.performance.cop_cycle > 0);
assert.equal(Object.keys(engine.createMollierPlotModel(mollier, completeCycle).points).length, 4);
assert.ok(completeCycle.diagnosis);
assert.ok(Array.isArray(completeCycle.diagnosis.observations));
assert.ok(completeCycle.diagnosis.next_check);

const underfeedDiagnosis = engine.interpretMollierCycle({
  cycle: {status: 'complete', errors: [], performance: {cop_cycle: 2.4}},
  measurements: {
    low_pressure: {result: {dew_temperature_c: 0}},
    suction_line_temperature: {value: 18},
    high_pressure: {result: {bubble_temperature_c: 40}},
    liquid_line_temperature: {value: 38},
    discharge_line_temperature: {value: 92},
  },
});
assert.equal(underfeedDiagnosis.values.superheat_k, 18);
assert.equal(underfeedDiagnosis.values.subcooling_k, 2);
assert.equal(underfeedDiagnosis.hypotheses[0].code, 'possible_underfeed');
assert.match(underfeedDiagnosis.next_check, /Confirmar ambas temperaturas/i);

const liquidReturnDiagnosis = engine.interpretMollierCycle({
  cycle: {status: 'complete', errors: [], performance: {cop_cycle: 3.1}},
  measurements: {
    low_pressure: {result: {dew_temperature_c: 8}},
    suction_line_temperature: {value: 9},
    high_pressure: {result: {bubble_temperature_c: 45}},
    liquid_line_temperature: {value: 37},
    discharge_line_temperature: {value: 80},
  },
});
assert.equal(liquidReturnDiagnosis.hypotheses[0].code, 'possible_liquid_return');
assert.equal(liquidReturnDiagnosis.hypotheses[0].level, 'danger');

const thermalStressDiagnosis = engine.interpretMollierCycle({
  cycle: {status: 'complete', errors: [], performance: {cop_cycle: 2.2}},
  measurements: {
    low_pressure: {result: {dew_temperature_c: 0}},
    suction_line_temperature: {value: 15},
    high_pressure: {result: {bubble_temperature_c: 44}},
    liquid_line_temperature: {value: 36},
    discharge_line_temperature: {value: 122},
  },
});
assert.ok(thermalStressDiagnosis.hypotheses.some(item => item.code === 'compressor_thermal_stress'));
assert.ok(thermalStressDiagnosis.observations.some(item => item.code === 'discharge_temperature' && item.level === 'danger'));

const inconsistentDiagnosis = engine.interpretMollierCycle({
  cycle: {status: 'complete', errors: [], performance: {cop_cycle: 3}},
  measurements: {
    low_pressure: {result: {dew_temperature_c: 8}},
    suction_line_temperature: {value: 3},
    high_pressure: {result: {bubble_temperature_c: 42}},
    liquid_line_temperature: {value: 47},
  },
});
assert.equal(inconsistentDiagnosis.status, 'review');
assert.equal(inconsistentDiagnosis.input_consistency, 'inconsistent');
assert.equal(inconsistentDiagnosis.hypotheses[0].code, 'measurement_inconsistency');
assert.match(inconsistentDiagnosis.next_check, /refrigerante.*manómetro/i);
assert.doesNotMatch(inconsistentDiagnosis.headline, /carga baja|restricción|exceso de alimentación/i);
assert.match(inconsistentDiagnosis.limitation, /revoluciones reales.*apertura interna/i);

assert.throws(
  () => engine.lookupMollierState({
    mollier, designation: 'R32', pressurePaAbs: r32High.pressure_pa_abs, temperatureC: 60, region: 'liquid',
  }),
  error => error.code === 'not_subcooled_liquid'
);

assert.throws(
  () => engine.convertPressureToTemperature({catalog, curves, designation: 'R744', pressure: 10}),
  error => error.code === 'unsupported_refrigerant'
);
assert.throws(
  () => engine.convertPressureToTemperature({catalog, curves, designation: 'R513B', pressure: 5}),
  error => error.code === 'unsupported_refrigerant'
);

console.log('Frigorista engine tests: OK');
