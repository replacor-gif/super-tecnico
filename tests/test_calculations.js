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
near(C.rectifiedBus(400, 0.9, 2, 50, 1, 1000e-6, 'three').noLoad, 400 * Math.SQRT2 - 1.8);
near(C.rectifiedBus(400, 0.9, 2, 50, 1, 1000e-6, 'three').rippleFrequency, 300);
near(C.ledArray(12, 2, 0.02, 3, 2).resistance, 300);
near(C.ledArray(12, 2, 0.02, 3, 2).totalCurrent, 0.04);
near(C.zenerResistor(12, 5.1, 0.02, 0.005).resistance, 276);
near(C.timer555Astable(10000, 100000, 10e-9).frequency, 1 / (Math.LN2 * 210000 * 10e-9));
near(C.timer555Bistable(12, 10000, 10000).setThreshold, 4);
near(C.ntcTemperatureFromResistance(10000, 10000, 3950), 25, 1e-8);
near(C.ntcResistanceFromTemperature(25, 10000, 3950), 10000, 1e-8);
assert.equal(C.windingBalance([1, 1, 1]).status, 'Equilibrado');
near(C.frequencyData(50, 2, 2).rpmFromPulses, 1500);
near(C.frequencyData(50, 2, 2).synchronousRpm, 1500);
const roomAir = C.ventilationAirflow(10, 8, 3, 8, 60, 0, 0);
near(roomAir.roomVolumeM3, 240);
near(roomAir.airflowM3h, 1920);
const cycledAir = C.ventilationAirflow(10, 8, 3, 8, 45, 15, 100);
near(cycledAir.activeFraction, 0.75);
near(cycledAir.airflowM3h, 2660);
const duct = C.ductSizing({
  airflowM3h: 2500,
  outletCount: 8,
  ductHeightCm: 25,
  ductVelocityMps: 3.7,
  grilleWidthCm: 35,
  grilleType: 'double',
});
assert.equal(duct.sections.length, 8);
assert.equal(duct.mainSection.recommendedWidthCm, 80);
assert.equal(duct.mainSection.smoothRoundMm, 500);
assert.equal(duct.mainSection.roughRoundMm, 630);
assert.equal(duct.recommendedGrilleHeightCm, 15);
near(duct.outletAirflowM3h, 312.5);
near(duct.mainSection.actualVelocityMps, 2500 / (0.8 * 0.25 * 3600));
assert.equal(duct.sections[7].recommendedWidthCm, 10);
assert.equal(duct.status, 'Velocidad equilibrada');

assert.throws(() => C.equivalent([1000, Number.NaN], 'R', 'series'));
assert.throws(() => C.ohmsLaw('VR', 230, 0));
assert.throws(() => C.rcTime(0, 100e-6));
assert.throws(() => C.ntcTemperatureFromResistance(-1, 10000, 3950));
assert.throws(() => C.windingBalance([1, 1, 0]));
assert.throws(() => C.ledArray(5, 3, 0.02, 2, 1));
assert.throws(() => C.zenerResistor(5, 5.1, 0.01, 0.005));
assert.throws(() => C.ventilationAirflow(0, 8, 3, 8));
assert.throws(() => C.ductSizing({ airflowM3h: 2500, outletCount: 0, ductHeightCm: 25, grilleWidthCm: 35 }));

console.log('Calculadoras: pruebas superadas.');
