'use strict';

const assert = require('node:assert/strict');
const D = require('../assets/duct-designer.js');

const state = D.exampleState();
const example = D.calculateProject(state);
assert.equal(example.totals.rooms, 6);
assert.equal(example.totals.selectedRooms, 3);
assert.equal(example.totals.connectedRooms, 3);
assert.equal(example.totals.conditionedAreaM2, 51);
assert.equal(example.totals.loadFg, 7650);
assert.equal(example.totals.suggestedCapacityFg, 8000);
assert.equal(example.totals.airflowM3h, 1020);
assert.equal(example.totals.mainDuct.widthCm, 31);
assert.ok(example.sections.length >= 3);
assert.ok(example.activeEdges.length > 0);
assert.ok(example.rooms.every(room => room.volumeM3 > 0));
assert.ok(example.rooms.find(room => room.id === 'bath').conditioned === false);
assert.ok(example.warnings.some(item => item.level === 'ok'));

const network = D.automaticNetwork(state);
assert.equal(network.outlets.length, 3);
assert.ok(network.routeEdges.length > 0);
assert.ok(network.outlets.every(outlet => state.rooms.some(room => room.id === outlet.roomId)));

const internalCriteria = D.calculateProject({
  ...D.emptyState(),
  loadPerM2: 999,
  airflowPer9000: 1,
  areaPer9000: 1,
  grilleMultiplier: 99,
  rooms: [{ id: 'office', type: 'office', name: 'Despacho', x: 1, y: 1, w: 4, h: 4, conditioned: true }],
  machine: { x: 1, y: 6 },
});
assert.equal(internalCriteria.rooms[0].areaM2, 4);
assert.equal(internalCriteria.rooms[0].loadFg, 600);
assert.equal(internalCriteria.rooms[0].airflowM3h, 80);
assert.equal(internalCriteria.state.loadPerM2, undefined);
assert.equal(internalCriteria.state.machineCapacityFg, undefined);

const duct9000 = D.sizeDuct(9000);
assert.equal(duct9000.widthCm, 36);
assert.equal(duct9000.heightCm, 25);
assert.equal(duct9000.airflowM3h, 1200);

assert.equal(D.roomOverlap({ x: 0, y: 0, w: 2, h: 2 }, { x: 1, y: 1, w: 2, h: 2 }), true);
assert.equal(D.roomOverlap({ x: 0, y: 0, w: 2, h: 2 }, { x: 2, y: 0, w: 2, h: 2 }), false);

const stepTwo = D.renderPlanSvg(example, { step: 2 });
assert.match(stepTwo.svg, /class="zone-toggle is-checked"/);
assert.match(stepTwo.svg, /SIN REJILLA/);
const stepThree = D.renderPlanSvg(example, { step: 3 });
assert.match(stepThree.svg, /class="installation-plan"/);
assert.match(stepThree.svg, /Dormitorio 1/);
assert.match(stepThree.svg, /UNIDAD INTERIOR/);
assert.match(stepThree.svg, /class="route-edge"/);
assert.match(stepThree.svg, /room-type-hallway/);

console.log('Asistente intuitivo de planos y conductos: pruebas superadas.');
