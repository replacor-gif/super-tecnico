'use strict';

const assert = require('node:assert/strict');
const D = require('../assets/duct-designer.js');

const state = D.exampleState();
const example = D.calculateProject(state);
assert.equal(example.totals.rooms, 6);
assert.equal(example.totals.identifiedRooms, 6);
assert.equal(example.totals.selectedRooms, 3);
assert.equal(example.totals.connectedRooms, 3);
assert.equal(example.totals.areaM2, 76);
assert.equal(example.totals.conditionedAreaM2, 46.5);
assert.equal(example.totals.loadFg, 6975);
assert.equal(example.totals.suggestedCapacityFg, 7000);
assert.equal(example.totals.airflowM3h, 930);
assert.equal(example.totals.mainDuct.widthCm, 28);
assert.equal(example.totals.mainDuct.heightCm, 25);
assert.ok(example.totals.hallwayLengthM > 0);
assert.ok(example.sections.some(section => section.isMain));
assert.ok(example.sections.some(section => !section.isMain));
assert.ok(example.activeEdges.filter(edge => edge.environment === 'hallway').length / example.activeEdges.length > .7);
assert.ok(example.warnings.some(item => item.level === 'ok'));

const network = D.automaticNetwork(state);
assert.equal(network.outlets.length, 3);
assert.equal(new Set(network.outlets.map(outlet => `${outlet.x},${outlet.y}`)).size, 3);
assert.ok(network.routeEdges.length > 0);

const internalCriteria = D.calculateProject({
  ...D.emptyState(),
  phase: 'configure',
  loadPerM2: 999,
  airflowPer9000: 1,
  areaPer9000: 1,
  grilleMultiplier: 99,
  ductHeightCm: 20,
  grilleHeightCm: 10,
  rooms: [{ id: 'office', type: 'office', points: [{ x: 1, y: 1 }, { x: 5, y: 1 }, { x: 5, y: 5 }, { x: 1, y: 5 }], conditioned: true }],
  machine: { roomId: 'office', x: 3, y: 3 },
});
assert.equal(internalCriteria.rooms[0].areaM2, 4);
assert.equal(internalCriteria.rooms[0].loadFg, 600);
assert.equal(internalCriteria.rooms[0].airflowM3h, 80);
assert.equal(internalCriteria.rooms[0].branchDuct.heightCm, 20);
assert.equal(internalCriteria.rooms[0].grille.heightCm, 10);
assert.equal(internalCriteria.state.loadPerM2, undefined);
assert.equal(internalCriteria.state.machineCapacityFg, undefined);

const duct9000 = D.sizeDuct(9000);
assert.equal(duct9000.widthCm, 36);
assert.equal(duct9000.heightCm, 25);
assert.equal(duct9000.airflowM3h, 1200);
assert.equal(D.sizeDuct(9000, { ductHeightCm: 30 }).widthCm, 30);

const irregular = [{ x: 0, y: 0 }, { x: 5, y: 0 }, { x: 5, y: 2 }, { x: 3, y: 4 }, { x: 0, y: 3 }];
assert.equal(D.polygonArea(irregular), 16.5);
assert.equal(D.polygonSelfIntersects(irregular), false);
assert.equal(D.polygonSelfIntersects([{ x: 0, y: 0 }, { x: 4, y: 4 }, { x: 0, y: 4 }, { x: 4, y: 0 }]), true);
assert.equal(D.pointInPolygon({ x: 2, y: 2 }, irregular), true);
assert.equal(D.roomOverlap({ points: irregular }, { points: [{ x: 4, y: 1 }, { x: 7, y: 1 }, { x: 7, y: 3 }, { x: 4, y: 3 }] }), true);
assert.equal(D.roomOverlap({ points: irregular }, { points: [{ x: 5, y: 0 }, { x: 8, y: 0 }, { x: 8, y: 2 }, { x: 5, y: 2 }] }), false);

const legacy = D.normalizeState({
  workflowStep: 3,
  rooms: [{ id: 'legacy', type: 'bedroom', x: 1, y: 2, w: 4, h: 3, conditioned: true }],
  machine: { x: 2, y: 3 },
});
assert.equal(legacy.phase, 'configure');
assert.equal(legacy.rooms[0].points.length, 4);
assert.equal(legacy.machine.roomId, 'legacy');

const drawing = D.renderPlanSvg(D.calculateProject(D.emptyState()), { drawingPoints: [{ x: 1, y: 1 }, { x: 6, y: 1 }, { x: 5, y: 5 }] });
assert.match(drawing.svg, /class="drawing-line"/);
assert.match(drawing.svg, /data-kind="close-polygon"/);
const configured = D.renderPlanSvg(example);
assert.match(configured.svg, /data-kind="room-type"/);
assert.match(configured.svg, /class="zone-toggle is-checked"/);
assert.match(configured.svg, /class="machine-toggle is-selected"/);
assert.match(configured.svg, /class="route-edge is-main through-hallway"/);
assert.match(configured.svg, /UNIDAD INTERIOR/);

console.log('Plano poligonal y red principal de conductos: pruebas superadas.');
