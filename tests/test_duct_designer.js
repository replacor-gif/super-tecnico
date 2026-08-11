'use strict';

const assert = require('node:assert/strict');
const D = require('../assets/duct-designer.js');

const state = D.exampleState();
const example = D.calculateProject(state);
assert.equal(example.totals.rooms, 6);
assert.equal(example.totals.conditionedRooms, 4);
assert.equal(example.totals.connectedRooms, 4);
assert.equal(example.totals.loadFg, 9450);
assert.equal(example.totals.suggestedCapacityFg, 9500);
assert.equal(example.totals.mainDuct.widthCm, 38);
assert.ok(example.sections.length >= 4);
assert.ok(example.sections[0].loadFg > example.sections.at(-1).loadFg);
assert.ok(example.rooms.every(room => room.volumeM3 > 0));
assert.ok(example.rooms.find(room => room.id === 'bath').conditioned === false);
assert.ok(example.warnings.some(item => item.level === 'ok'));

const disconnected = D.calculateProject({
  ...D.emptyState(),
  rooms: [{ id: 'office', type: 'office', name: 'Despacho', x: 1, y: 1, w: 6, h: 5, conditioned: true }],
  machine: { x: 2, y: 7 },
  outlets: [{ id: 'out', roomId: 'office', x: 3, y: 5 }],
});
assert.equal(disconnected.totals.connectedRooms, 0);
assert.ok(disconnected.warnings.some(item => item.text.includes('no está unida')));

const route = D.routeEdgesFromPoints({ x: 1, y: 1 }, { x: 4, y: 3 });
assert.equal(route.length, 5);
assert.ok(route.every(edge => Math.abs(edge.a.x - edge.b.x) + Math.abs(edge.a.y - edge.b.y) === 1));

assert.equal(D.roomOverlap({ x: 0, y: 0, w: 2, h: 2 }, { x: 1, y: 1, w: 2, h: 2 }), true);
assert.equal(D.roomOverlap({ x: 0, y: 0, w: 2, h: 2 }, { x: 2, y: 0, w: 2, h: 2 }), false);

const rendered = D.renderPlanSvg(example);
assert.match(rendered.svg, /class="installation-plan"/);
assert.match(rendered.svg, /Dormitorio principal/);
assert.match(rendered.svg, /UNIDAD INTERIOR/);
assert.match(rendered.svg, /data-kind="section"/);
assert.match(rendered.svg, /room-type-hallway/);

console.log('Editor profesional de planos y conductos: pruebas superadas.');
