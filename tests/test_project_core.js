'use strict';

const assert = require('node:assert/strict');
const memory = new Map();
global.localStorage = {
  getItem: key => memory.has(key) ? memory.get(key) : null,
  setItem: (key, value) => memory.set(key, String(value)),
  removeItem: key => memory.delete(key),
};
global.window = global;
global.location = { pathname: '/super-tecnico/test.html' };
global.CustomEvent = class CustomEvent { constructor(type, options) { this.type = type; this.detail = options?.detail; } };
global.dispatchEvent = () => true;
require('../assets/project-core.js');

const API = global.SuperTecnicoProjects;
assert.ok(API);
const project = API.create({ name: 'Obra de prueba', discipline: 'climatizacion', location: 'Madrid' });
assert.equal(API.get().id, project.id);
assert.equal(API.summary().project_count, 1);

API.attachArtifact({
  module_id: 'ducts', title: 'Conductos', summary: 'Red principal',
  measurements: [
    { code: 'DUCT-20X20', description: 'Conducto 20 × 20 cm', unit: 'm', quantity: 8.5 },
    { code: 'GRILLE-40X15', description: 'Rejilla 40 × 15 cm', unit: 'ud', quantity: 2 },
  ], snapshot: { rooms: 3 },
});
API.attachArtifact({
  module_id: 'ventilation', title: 'Ventilación',
  measurements: [{ code: 'DUCT-20X20', description: 'Conducto 20 × 20 cm', unit: 'm', quantity: 3.5 }], snapshot: {},
});
assert.equal(API.get().artifacts.length, 2);
const measurements = API.aggregateMeasurements(API.get());
assert.equal(measurements.find(item => item.code === 'DUCT-20X20').quantity, 12);
assert.equal(API.exportProject().pricing_status, 'unpriced_measurements_only');

API.attachArtifact({ module_id: 'ducts', title: 'Conductos revisados', measurements: [], snapshot: {} });
assert.equal(API.get().artifacts.length, 2);
assert.equal(API.get().artifacts.find(item => item.module_id === 'ducts').title, 'Conductos revisados');
assert.equal(API.remove(project.id), true);
assert.equal(API.list().length, 0);
console.log('Proyecto Técnico: almacenamiento, sustitución y mediciones superados.');
