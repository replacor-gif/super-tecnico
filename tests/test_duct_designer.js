'use strict';

const assert = require('node:assert/strict');
const D = require('../assets/duct-designer.js');

const example = D.calculateProject(D.exampleState());
assert.equal(example.totals.rooms, 6);
assert.equal(example.totals.loadFg, 11619);
assert.equal(example.totals.suggestedCapacityFg, 12000);
assert.equal(example.totals.mainDuct.widthCm, 47);
assert.equal(example.sides.left.sections.length, 3);
assert.equal(example.sides.right.sections.length, 3);
assert.equal(example.sides.left.sections[0].widthCm, 18);
assert.equal(example.sides.right.sections[0].widthCm, 30);
assert.ok(example.sides.right.sections[0].loadFg > example.sides.right.sections[1].loadFg);
assert.ok(example.sides.right.sections[1].loadFg > example.sides.right.sections[2].loadFg);
assert.equal(example.sides.right.rooms[0].grille.widthCm, 55);

const manual = D.calculateProject({
  ...D.emptyState(),
  machineCapacityFg: 2000,
  rooms: [{ id: 'manual', side: 'left', name: 'Taller', widthM: 3, lengthM: 3, manualLoadFg: 3500 }],
});
assert.equal(manual.totals.loadFg, 3500);
assert.equal(manual.sides.left.rooms[0].source, 'manual');
assert.ok(manual.warnings.some(item => item.level === 'danger'));

const rendered = D.renderDiagramSvg(example);
assert.ok(rendered.width >= 1000);
assert.match(rendered.svg, /class="duct-network-svg"/);
assert.match(rendered.svg, /Dormitorio 1/);
assert.match(rendered.svg, /Salón/);
assert.match(rendered.svg, /data-inspect-kind="section"/);

console.log('Diseñador de conductos: pruebas superadas.');
