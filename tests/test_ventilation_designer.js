'use strict';

const assert = require('node:assert/strict');
const V = require('../assets/ventilation-designer.js');
const Rules = require('../assets/ventilation-rules.js');

assert.equal(Rules.PROFILES.cte_garage.lpsPerSpace, 120);
assert.equal(Rules.PROFILES.rite_ida2_people.lpsPerPerson, 12.5);
assert.equal(Rules.PROFILES.rite_service_extract.lpsPerM2, 2);
assert.equal(Rules.SOURCES.cteHs3.checked, '2026-08-17');

const example = V.calculateProject(V.exampleState());
assert.equal(example.totals.rooms, 6);
assert.equal(example.totals.terminals, 5);
assert.equal(example.totals.connectedTerminals, 5);
assert.equal(example.totals.supplyLps, 20);
assert.equal(example.totals.extractLps, 24);
assert.equal(example.totals.supplyM3h, 72);
assert.equal(example.totals.extractM3h, 86.4);
assert.ok(example.fanResults.every(fan => fan.longestRunM > 0));
assert.equal(example.rooms.find(room => room.id === 'main-bed').supplyLps, 8);
assert.equal(example.rooms.find(room => room.id === 'bed').supplyLps, 4);
assert.equal(example.rooms.find(room => room.id === 'living').supplyLps, 8);
assert.equal(example.rooms.find(room => room.id === 'bath').extractLps, 12);
assert.equal(example.rooms.find(room => room.id === 'kitchen').extractLps, 12);
assert.ok(example.sections.length > 0);
assert.ok(example.sections.every(section => section.widthCm % 5 === 0 && section.heightCm % 5 === 0));
assert.ok(example.activeEdges.filter(edge => edge.environment === 'hallway').length > 0);
assert.ok(example.warnings.some(item => /50 l\/s/.test(item.text)));

const dwellingExtractOnly = V.calculateProject({ ...V.exampleState(), systemMode: 'extract' });
assert.equal(dwellingExtractOnly.totals.supplyLps, 0);
assert.equal(dwellingExtractOnly.totals.extractLps, 24);
assert.ok(dwellingExtractOnly.warnings.some(item => /aberturas de admisi/i.test(item.text)));

const officeState = V.normalizeState({
  phase: 'equipment',
  profileId: 'rite_ida2_people',
  systemMode: 'balanced',
  cellSizeM: 1,
  defaultHeightM: 3,
  rooms: [{ id: 'office', type: 'office', heightM: 3, occupants: 4, points: [{ x: 1, y: 1 }, { x: 6, y: 1 }, { x: 6, y: 5 }, { x: 1, y: 5 }] }],
  terminals: [
    { id: 'office-supply', kind: 'supply', x: 2, y: 2 },
    { id: 'office-extract', kind: 'extract', x: 5, y: 4 },
  ],
  fans: [
    { id: 'office-fan-supply', kind: 'supply', x: 1, y: 7 },
    { id: 'office-fan-extract', kind: 'extract', x: 7, y: 7 },
  ],
});
const office = V.calculateProject(officeState);
assert.equal(office.rooms[0].areaM2, 20);
assert.equal(office.rooms[0].volumeM3, 60);
assert.equal(office.rooms[0].supplyLps, 50);
assert.equal(office.rooms[0].extractLps, 50);
assert.equal(office.totals.supplyM3h, 180);
assert.equal(office.totals.extractM3h, 180);
assert.equal(office.totals.connectedTerminals, 2);

const service = V.calculateProject({
  ...officeState,
  profileId: 'rite_service_extract',
  systemMode: 'extract',
  terminals: [{ id: 'service-extract', kind: 'extract', x: 3, y: 3 }],
  fans: [{ id: 'service-fan', kind: 'extract', x: 7, y: 7 }],
});
assert.equal(service.rooms[0].extractLps, 40);
assert.equal(service.totals.extractM3h, 144);

const garage = V.calculateProject({
  ...officeState,
  profileId: 'cte_garage',
  systemMode: 'extract',
  rooms: [{ ...officeState.rooms[0], id: 'garage', type: 'garage', parkingSpaces: 2 }],
  terminals: [{ id: 'garage-extract', kind: 'extract', roomId: 'garage', x: 3, y: 3 }],
  fans: [{ id: 'garage-fan', kind: 'extract', x: 7, y: 7 }],
});
assert.equal(garage.rooms[0].extractLps, 240);
assert.equal(garage.totals.extractM3h, 864);

const ach = V.calculateProject({
  ...officeState,
  profileId: 'technical_ach',
  systemMode: 'extract',
  customAch: 6,
  terminals: [{ id: 'ach-extract', kind: 'extract', x: 3, y: 3 }],
  fans: [{ id: 'ach-fan', kind: 'extract', x: 7, y: 7 }],
});
assert.equal(ach.rooms[0].volumeM3, 60);
assert.equal(ach.rooms[0].extractLps, 100);
assert.equal(ach.totals.extractM3h, 360);
assert.ok(ach.warnings.some(item => /no justifican por sí solas/i.test(item.text)));

const duct100 = V.chooseRectangularSize(100);
assert.ok(duct100.areaCm2 >= 250);
assert.ok(duct100.velocityMps <= 4);
assert.equal(duct100.widthCm % 5, 0);
assert.equal(duct100.heightCm % 5, 0);
const grille100 = V.chooseGrilleSize(100);
assert.ok(grille100.areaCm2 >= 500);
assert.ok(grille100.velocityMps <= 2);

const drawing = V.renderPlanSvg(example);
assert.match(drawing.svg, /class="vent-route route-supply/);
assert.match(drawing.svg, /class="vent-route route-extract/);
assert.match(drawing.svg, /data-kind="vent-terminal"/);
assert.match(drawing.svg, /data-kind="vent-fan"/);
assert.match(drawing.svg, /TURBINA I/);
assert.match(drawing.svg, /TURBINA E/);

console.log('Ventilación y extracción: cálculo, redes y normativa base superados.');
