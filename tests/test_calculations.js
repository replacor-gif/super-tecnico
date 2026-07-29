'use strict';

const assert = require('node:assert/strict');
const C = require('../assets/calculations.js');

function near(actual, expected, tolerance = 1e-9) {
  assert.ok(
    Math.abs(actual - expected) <= tolerance * Math.max(1, Math.abs(expected)),
    `${actual} != ${expected}`,
  );
}

near(C.ohmsLaw('VR', 230, 100).I, 2.3);
near(C.resistorColors(['marron', 'negro', 'rojo', 'oro']).value, 1000);
near(C.smdResistorCode('472').value, 4700);
near(C.smdResistorCode('1001').value, 1000);
near(C.smdResistorCode('4R7').value, 4.7);
near(C.smdResistorCode('01C').value, 10000);
near(C.capacitorCode('104K').farads, 100e-9);
near(C.equivalent([1000, 1000], 'R', 'parallel'), 500);
near(C.equivalent([1e-6, 1e-6], 'C', 'series'), 0.5e-6);
near(C.voltageDivider(12, 27000, 10000, NaN).noLoad, 12 * 10000 / 37000);
near(C.rcTime(10000, 100e-6).tau, 1);
near(C.rectifiedBus(230, 0.9, 2, 50, 0, 0).noLoad, 230 * Math.SQRT2 - 1.8);
near(C.ntcTemperatureFromResistance(10000, 10000, 3950), 25, 1e-8);
near(C.ntcResistanceFromTemperature(25, 10000, 3950), 10000, 1e-8);
assert.equal(C.windingBalance([1, 1, 1]).status, 'Equilibrado');
near(C.frequencyData(50, 2, 2).rpmFromPulses, 1500);
near(C.frequencyData(50, 2, 2).synchronousRpm, 1500);

assert.throws(() => C.equivalent([1000, Number.NaN], 'R', 'series'));
assert.throws(() => C.ohmsLaw('VR', 230, 0));
assert.throws(() => C.rcTime(0, 100e-6));
assert.throws(() => C.ntcTemperatureFromResistance(-1, 10000, 3950));
assert.throws(() => C.windingBalance([1, 1, 0]));

console.log('Calculadoras: pruebas superadas.');
