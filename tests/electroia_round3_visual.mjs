import assert from "node:assert/strict";
import { mkdir } from "node:fs/promises";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const core = require("../archivo-tecnico-47097e44267b9cb111636b84823f1d47/diagram-core.js");
const expected = new Map([
  ["Sensores y transductores", 42],
  ["Medida e indicación", 12],
  ["Conectores y comunicaciones", 19],
]);
const registryResult = core.getRegistry();
assert.equal(registryResult.engine_version, "1.17.0-alpha.1");
const registry = registryResult.symbols;
for (const [category, count] of expected) {
  const family = registry.filter((symbol) => symbol.category === category);
  assert.equal(family.length, count, category);
  assert.ok(family.every((symbol) => symbol.review_status === "engine_reviewed"), `${category} mantiene borradores`);
  assert.ok(family.every((symbol) => Object.keys(symbol.ports).length >= 1), `${category} tiene símbolos sin terminales`);
  for (const symbol of family) {
    for (const [portName, port] of Object.entries(symbol.ports)) {
      const onVerticalEdge = Math.abs(port.x) === symbol.width / 2;
      const onHorizontalEdge = Math.abs(port.y) === symbol.height / 2;
      assert.ok(onVerticalEdge || onHorizontalEdge, `${symbol.id}.${portName} no está en el borde`);
    }
  }
}

const selectedIds = [
  "SYM-0168", "SYM-0177", "SYM-0349", "SYM-0441",
  "SYM-0139", "SYM-0142", "SYM-0148", "SYM-0434",
  "SYM-0256", "SYM-0260", "SYM-0264", "SYM-0267",
];
const selected = selectedIds.map((id) => registry.find((symbol) => symbol.id === id));
assert.ok(selected.every(Boolean));
assert.deepEqual(Object.keys(selected[1].ports), ["A", "B", "Z", "VCC", "GND"]);
assert.deepEqual(Object.keys(selected[3].ports), ["REF+", "REF-", "SIN+", "SIN-", "COS+", "COS-"]);
assert.deepEqual(Object.keys(selected[5].ports), ["I+", "V+", "I-", "V-"]);
assert.deepEqual(Object.keys(selected[10].ports), ["VBUS", "D+", "D-", "GND", "SHIELD"]);

const components = selected.map((symbol, index) => ({
  ref: `X${index + 1}`,
  display_ref: symbol.id,
  symbol_id: symbol.id,
  value: symbol.name,
  position: { x: 10 + (index % 4) * 23, y: 10 + Math.floor(index / 4) * 18 },
}));
const nets = components.map((component, index) => ({
  id: `N${index + 1}`,
  show_label: false,
  connections: [`${component.ref}.${Object.keys(selected[index].ports)[0]}`],
}));
const result = core.render({
  schema_version: "1.0",
  document_kind: "circuit_diagram",
  standard_profile: "IEC_EXPERIMENTAL",
  title: "ElectroIA · normalización masiva 3",
  document_id: "ELECTROIA-ROUND3-REVIEW",
  revision: "A",
  components,
  nets,
});
assert.equal(result.diagnostics.errors.length, 0);
assert.doesNotMatch(result.svg, /class="component review-auto_draft"/);
assert.match(result.svg, />S<\/text>/);
assert.match(result.svg, />M<\/text>/);
assert.match(result.svg, />X<\/text>/);

await mkdir("test-artifacts", { recursive: true });
const browser = await chromium.launch({
  headless: true,
  executablePath: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  args: ["--disable-gpu", "--no-first-run"],
});
const page = await browser.newPage({ viewport: { width: 1600, height: 980 }, deviceScaleFactor: 1 });
await page.setContent(`<style>body{margin:0;background:#e9ece9}svg{display:block;width:100%;height:auto}</style>${result.svg}`);
await page.screenshot({ path: "test-artifacts/electroia-round3-reviewed.png", fullPage: true });
await browser.close();
process.stdout.write("ElectroIA round-three visual: 73 reviewed symbols OK\n");
