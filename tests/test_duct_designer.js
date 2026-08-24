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
assert.equal(example.totals.loadFg, 6000);
assert.equal(example.totals.suggestedCapacityFg, 6000);
assert.equal(example.totals.airflowM3h, 800);
assert.equal(example.totals.mainDuct.widthCm, 25);
assert.equal(example.totals.mainDuct.heightCm, 25);
assert.ok(example.totals.hallwayLengthM > 0);
assert.ok(example.sections.some(section => section.isMain));
assert.ok(example.sections.some(section => !section.isMain));
assert.ok(example.activeEdges.filter(edge => edge.environment === 'hallway').length / example.activeEdges.length > .7);
assert.ok(example.warnings.some(item => item.level === 'ok'));
assert.ok(example.activeEdges.every(edge => edge.widthCm % 5 === 0 && edge.heightCm % 5 === 0));

const network = D.automaticNetwork(state);
assert.equal(network.outlets.length, 3);
assert.equal(new Set(network.outlets.map(outlet => `${outlet.x},${outlet.y}`)).size, 3);
assert.ok(network.routeEdges.length > 0);
network.outlets.forEach(outlet => {
  const room = state.rooms.find(item => item.id === outlet.roomId);
  const wall = D.wallSegments(room).find(item => item.index === outlet.wallIndex);
  assert.ok(wall, `Missing wall for ${outlet.roomId}`);
  assert.equal(outlet.x, wall.x, `${outlet.roomId} grille is not horizontally centred`);
  assert.equal(outlet.y, wall.y, `${outlet.roomId} grille is not vertically centred`);
  assert.equal(outlet.wallAngleDeg, wall.angleDeg, `${outlet.roomId} grille is not aligned with its wall`);
  assert.equal(outlet.centered, true);
  assert.ok(network.routeEdges.some(edge => `${edge.a.x},${edge.a.y}` === `${outlet.x},${outlet.y}` || `${edge.b.x},${edge.b.y}` === `${outlet.x},${outlet.y}`), `Branch does not end at ${outlet.roomId} grille`);
});

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
assert.equal(internalCriteria.rooms[0].loadFg, 2000);
assert.equal(Math.round(internalCriteria.rooms[0].airflowM3h), 267);
assert.equal(internalCriteria.rooms[0].branchDuct.heightCm, 20);
assert.equal(internalCriteria.rooms[0].grille.widthCm, 40);
assert.equal(internalCriteria.rooms[0].grille.heightCm, 10);
assert.equal(internalCriteria.state.loadPerM2, undefined);
assert.equal(internalCriteria.state.machineCapacityFg, undefined);

const duct9000 = D.sizeDuct(9000);
assert.equal(duct9000.widthCm, 35);
assert.equal(duct9000.heightCm, 25);
assert.equal(duct9000.airflowM3h, 1200);
assert.equal(D.sizeDuct(9000, { ductHeightCm: 30 }).widthCm, 30);
assert.equal(D.sizeDuct(9000, { ductHeightCm: 23 }).heightCm, 25);

const fixedLoads = D.normalizeState({
  phase: 'configure',
  rooms: [
    { id: 'bed', type: 'bedroom', conditioned: true, points: [{ x: 0, y: 0 }, { x: 3, y: 0 }, { x: 3, y: 3 }, { x: 0, y: 3 }] },
    { id: 'office', type: 'office', conditioned: true, points: [{ x: 3, y: 0 }, { x: 6, y: 0 }, { x: 6, y: 3 }, { x: 3, y: 3 }] },
    { id: 'living-normal', type: 'living', loadTier: 'normal', conditioned: true, points: [{ x: 0, y: 3 }, { x: 3, y: 3 }, { x: 3, y: 6 }, { x: 0, y: 6 }] },
    { id: 'living-large', type: 'living', loadTier: 'large', conditioned: true, points: [{ x: 3, y: 3 }, { x: 6, y: 3 }, { x: 6, y: 6 }, { x: 3, y: 6 }] },
    { id: 'kitchen-xl', type: 'kitchen', loadTier: 'veryLarge', conditioned: true, points: [{ x: 6, y: 3 }, { x: 9, y: 3 }, { x: 9, y: 6 }, { x: 6, y: 6 }] },
  ],
});
assert.deepEqual(fixedLoads.rooms.map(D.loadForRoom), [1500, 2000, 3000, 4500, 6000]);

const irregular = [{ x: 0, y: 0 }, { x: 5, y: 0 }, { x: 5, y: 2 }, { x: 3, y: 4 }, { x: 0, y: 3 }];
assert.equal(D.polygonArea(irregular), 16.5);
assert.equal(D.polygonSelfIntersects(irregular), false);
assert.equal(D.polygonSelfIntersects([{ x: 0, y: 0 }, { x: 4, y: 4 }, { x: 0, y: 4 }, { x: 4, y: 0 }]), true);
assert.equal(D.pointInPolygon({ x: 2, y: 2 }, irregular), true);
assert.equal(D.roomOverlap({ points: irregular }, { points: [{ x: 4, y: 1 }, { x: 7, y: 1 }, { x: 7, y: 3 }, { x: 4, y: 3 }] }), true);
assert.equal(D.roomOverlap({ points: irregular }, { points: [{ x: 5, y: 0 }, { x: 8, y: 0 }, { x: 8, y: 2 }, { x: 5, y: 2 }] }), false);

const diagonalRoom = { points: [{ x: 0, y: 0 }, { x: 5, y: 3 }, { x: 5, y: 7 }, { x: 0, y: 7 }] };
const diagonalPlacement = D.snapOutletToWall(diagonalRoom, { x: 3, y: 2 });
assert.deepEqual({ x: diagonalPlacement.x, y: diagonalPlacement.y }, { x: 2.5, y: 1.5 });
assert.equal(diagonalPlacement.wallIndex, 0);
assert.equal(diagonalPlacement.centered, true);
assert.ok(Math.abs(diagonalPlacement.wallAngleDeg - 30.96) < .01);

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
const configuration = D.renderPlanSvg(D.calculateProject({ ...state, phase: 'configure' }));
assert.match(configuration.svg, /data-kind="room-type"/);
assert.match(configuration.svg, /data-kind="room-load"/);
assert.match(configuration.svg, /class="zone-toggle is-checked"/);
assert.match(configuration.svg, /class="machine-toggle is-selected"/);
const mobileConfiguration = D.renderPlanSvg(D.calculateProject({ ...state, phase: 'configure' }), { compactConfigure: true, selectedRoomId: 'bed-1' });
assert.doesNotMatch(mobileConfiguration.svg, /data-kind="room-type"/);
assert.match(mobileConfiguration.svg, /data-kind="room-select"/);
assert.match(mobileConfiguration.svg, /is-context-selected/);
const configured = D.renderPlanSvg(example);
assert.doesNotMatch(configured.svg, /room-area-label/);
assert.doesNotMatch(configured.svg, /data-kind="room-type"/);
assert.match(configured.svg, /room-hatch-bedroom/);
assert.match(configured.svg, /class="route-edge is-main through-hallway"/);
assert.match(configured.svg, /data-kind="outlet-drag"/);
assert.match(configured.svg, /data-kind="branch-drag"/);
assert.match(configured.svg, /data-kind="trunk-drag"/);
assert.match(configured.svg, /UNIDAD INTERIOR/);
const selectedOnTouch = D.renderPlanSvg(example, { selectedAdjustment: { kind: 'outlet-drag', roomId: 'bed-1' } });
assert.match(selectedOnTouch.svg, /plan-outlet is-draggable is-selected/);
assert.match(selectedOnTouch.svg, /data-centered="true"/);
assert.match(selectedOnTouch.svg, /centrada y alineada con la pared/);
assert.match(selectedOnTouch.svg, /rotate\((?:0|90|30\.96)\)/);
assert.equal((selectedOnTouch.svg.match(/data-kind="outlet-wall-target"/g) || []).length, 4);
assert.match(selectedOnTouch.svg, /wall-snap-target is-current/);

const movedState = D.normalizeState({
  ...state,
  phase: 'layout',
  outletOverrides: { 'bed-1': { x: 7.8, y: 4 } },
  branchGuides: { 'bed-1': { x: 9, y: 5 } },
  trunkGuide: { x: 8, y: 12 },
});
const moved = D.calculateProject(movedState);
assert.deepEqual(moved.outletMap.get('bed-1'), {
  id: 'outlet-bed-1', roomId: 'bed-1', x: 8, y: 4, wallIndex: 1, wallAngleDeg: 90,
  wallA: { x: 8, y: 1 }, wallB: { x: 8, y: 7 }, centered: true,
});
assert.deepEqual(moved.roomConnections.get('bed-1').branchHandle, { x: 9, y: 5 });
assert.deepEqual(moved.state.trunkGuide, { x: 8, y: 12 });
assert.deepEqual(moved.trunkHandle, { x: 8, y: 12 });
assert.ok(moved.activeEdges.some(edge => [edge.a, edge.b].some(point => point.x === 8 && point.y === 12)), 'El principal no respeta el punto de paso manual');
assert.match(D.renderPlanSvg(moved, { selectedAdjustment: { kind: 'trunk-drag', roomId: 'main' } }).svg, /trunk-drag is-selected/);

console.log('Plano poligonal y red principal de conductos: pruebas superadas.');
