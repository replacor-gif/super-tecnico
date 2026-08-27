import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { callElectroIATool } from "../electroia-tool-server/src/toolkit.mjs";

const benchmark = JSON.parse(await readFile(new URL("../data/electroia/professional-benchmark.json", import.meta.url), "utf8"));
let totalBomRows = 0;
let totalTerminals = 0;
let totalIo = 0;

for (const item of benchmark.cases) {
  const first = await callElectroIATool("electroia_compile_diagram", { spec: item.spec });
  const second = await callElectroIATool("electroia_compile_diagram", { spec: item.spec });
  const dossier = first.technical_package;
  assert.equal(dossier.schema_version, "1.0", item.id);
  assert.equal(dossier.summary.components, first.diagram.document.components.length, item.id);
  assert.equal(dossier.summary.nets, first.diagram.document.nets.length, item.id);
  assert.equal(dossier.summary.errors, 0, item.id);
  assert.equal(dossier.wire_schedule.length, first.diagram.document.nets.length, item.id);
  assert.equal(new Set(dossier.wire_schedule.map((wire) => wire.wire_number)).size, dossier.wire_schedule.length, item.id);
  assert.equal(JSON.stringify(dossier), JSON.stringify(second.technical_package), `${item.id}: el dossier debe ser determinista`);
  totalBomRows += dossier.bom.length;
  totalTerminals += dossier.terminal_schedule.length;
  totalIo += dossier.io_schedule.length;
}

const documented = await callElectroIATool("electroia_compile_diagram", {
  spec: {
    title: "Lazo de presión documentado",
    document_id: "ELECTROIA-DOC-001",
    components: [
      { id: "psu", symbol_id: "SYM-0018", ref: "PS1", value: "24 VDC", location: "Cuadro CP1" },
      { id: "sensor", symbol_id: "SYM-0166", ref: "PT1", value: "4–20 mA", location: "Conducto impulsión" },
      { id: "input", symbol_id: "SYM-0465", ref: "AI1", exact_model: "Módulo AI documentado", location: "Cuadro CP1" },
    ],
    nets: [
      { id: "P24", role: "power", wire_number: "101", conductor_size_mm2: 0.75, color: "rojo", cable_id: "CBL-01", cable_type: "2x0,75 mm² apantallado", voltage: "24 VDC", connections: ["psu.+", "sensor.V+", "input.L+"] },
      { id: "M24", role: "ground", wire_number: "102", conductor_size_mm2: 0.75, color: "azul", cable_id: "CBL-01", cable_type: "2x0,75 mm² apantallado", voltage: "0 VDC", connections: ["psu.-", "sensor.GND", "input.MANA", "input.AI0-"] },
      { id: "PRESSURE", role: "signal", wire_number: "103", conductor_size_mm2: 0.75, color: "blanco", cable_id: "CBL-01", cable_type: "2x0,75 mm² apantallado", signal_type: "4–20 mA", io_address: "AIW64", connections: ["sensor.OUT", "input.AI0+"] },
    ],
  },
});

assert.equal(documented.technical_package.cable_schedule.length, 1);
assert.equal(documented.technical_package.cable_schedule[0].cable_id, "CBL-01");
assert.equal(documented.technical_package.wire_schedule[2].conductor_size_mm2, 0.75);
assert.equal(documented.technical_package.io_schedule.find((item) => item.ref === "AI1" && item.channel === "AI0+")?.address, "AIW64");
assert.equal(documented.technical_package.terminal_schedule.find((item) => item.ref === "PT1")?.location, "Conducto impulsión");

const regenerated = await callElectroIATool("electroia_generate_technical_package", { document: documented.diagram.document });
assert.deepEqual(regenerated.technical_package, documented.technical_package);

console.log(`ElectroIA technical package: OK · 20 proyectos · ${totalBomRows} partidas BOM · ${totalTerminals} terminales · ${totalIo} puntos E/S`);
