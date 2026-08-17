const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = path.resolve(__dirname, '..');
const properties = JSON.parse(fs.readFileSync(path.join(root, 'data/refrigerant-piping/property-grid.json'), 'utf8'));
const rules = JSON.parse(fs.readFileSync(path.join(root, 'data/refrigerant-piping/design-rules.json'), 'utf8'));
const context = { window: {} };
vm.runInNewContext(fs.readFileSync(path.join(root, 'assets/refrigerant-piping-engine.js'), 'utf8'), context);
const engine = context.window.RefrigerantPipingEngine;

function design(overrides = {}) {
  return engine.design({
    systemType: 'split', refrigerant: 'R32', capacityKw: 3.5, minimumLoadPercent: 35,
    evaporatingC: 5, condensingC: 45, lengthM: 10, verticalRiseM: 3,
    routeComplexity: 'normal', location: 'inside', ambientTemperatureC: 30,
    relativeHumidityPercent: 65, insulationConductivityWMK: 0.036,
    ...overrides,
  }, { properties, rules });
}

const split = design();
assert.equal(split.resultLevel, 'manufacturer_required');
assert.equal(split.oilManagement.status, 'fabricante_obligatorio');
assert.equal(split.lines.find(line => line.kind === 'suction').doubleRiser, null);
assert.equal(split.oilManagement.totalProposedTraps, 0);
const splitSuctionInsulation = split.insulation.find(item => item.line === 'suction');
assert.equal(splitSuctionInsulation.regulatoryReferenceMm, 10);
assert(splitSuctionInsulation.thicknessMm >= 9);
assert(split.warnings.some(item => item.includes('A2L')));

const central = design({
  systemType: 'central', refrigerant: 'R449A', capacityKw: 45, minimumLoadPercent: 15,
  evaporatingC: -10, condensingC: 40, lengthM: 38, verticalRiseM: 12,
});
const suction = central.lines.find(line => line.kind === 'suction');
assert(suction.doubleRiser);
assert(central.lines.some(line => line.kind === 'discharge'));
assert(central.oilManagement.totalProposedTraps >= 2);
assert(central.billOfQuantities.some(item => item.code === 'RP-DOUBLE-RISER'));
assert(central.billOfQuantities.filter(item => item.description.includes('doble montante')).length >= 2);

for (const result of [split, central]) {
  assert(result.lines.every(line => Number.isFinite(line.odMm) && Number.isFinite(line.velocityFullMS)));
  assert(result.billOfQuantities.every(item => item.quantity > 0));
  assert(result.billOfQuantities.every(item => !('unitPrice' in item) && !('amount' in item)));
  assert(result.lines.every(line => rules.pipe_material.sizes.some(size => size.od_mm === line.odMm)));
}

process.stdout.write('Refrigerant piping engine: thermodynamics, oil, insulation and unpriced BoQ OK\n');
