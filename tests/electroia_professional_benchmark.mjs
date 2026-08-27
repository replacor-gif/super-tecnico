import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { callElectroIATool } from "../electroia-tool-server/src/toolkit.mjs";

const catalog = JSON.parse(await readFile(new URL("../data/electroia/professional-benchmark.json", import.meta.url), "utf8"));
const domains = new Map();
const failures = [];
const totals = { symbols: 0, nets: 0, crossings: 0, automatic_matches: 0 };

assert.equal(catalog.cases.length, 20, "El banco profesional debe contener 20 casos");

for (const item of catalog.cases) {
  domains.set(item.domain, (domains.get(item.domain) || 0) + 1);
  try {
    const first = await callElectroIATool("electroia_compile_diagram", { spec: item.spec });
    const second = await callElectroIATool("electroia_compile_diagram", { spec: item.spec });
    assert.equal(first.ok, true);
    assert.equal(first.diagram.diagnostics.errors.length, 0);
    assert.equal(first.diagram.diagnostics.metrics.component_overlaps, 0);
    assert.equal(first.diagram.diagnostics.metrics.wire_component_conflicts, 0);
    assert.equal(first.diagram.diagnostics.metrics.pages, 1);
    assert.equal(first.diagram.svg, second.diagram.svg, "La salida debe ser determinista");
    assert.match(first.diagram.svg, /<svg[^>]+electroia-core-diagram/);
    totals.symbols += first.diagram.diagnostics.metrics.symbols;
    totals.nets += first.diagram.diagnostics.metrics.nets;
    totals.crossings += first.diagram.diagnostics.metrics.bridged_crossings;
    totals.automatic_matches += first.resolution.summary.automatic_symbol_matches;
  } catch (error) {
    failures.push(`${item.id}: ${error.message}`);
  }
}

for (const domain of catalog.domains) assert.equal(domains.get(domain), 5, `${domain} debe aportar 5 casos`);
assert.deepEqual(failures, [], failures.join("\n"));
assert.ok(totals.automatic_matches >= 4, "El banco debe probar resolución automática de símbolos en los cuatro ámbitos");

console.log(`ElectroIA professional benchmark: OK · ${catalog.cases.length} casos · ${totals.symbols} símbolos · ${totals.nets} redes · ${totals.crossings} cruces salvados · ${totals.automatic_matches} búsquedas automáticas`);
