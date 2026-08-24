import assert from "node:assert/strict";
import { mkdir } from "node:fs/promises";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const core = require("../archivo-tecnico-47097e44267b9cb111636b84823f1d47/diagram-core.js");

const registryResult = core.getRegistry();
assert.equal(registryResult.version, "0.9");
assert.equal(registryResult.engine_version, "1.14.1-alpha.1");
const registry = registryResult.symbols;
const newlyReviewedIds = [
  "SYM-0163", "SYM-0164", "SYM-0165", "SYM-0166", "SYM-0167", "SYM-0170",
  "SYM-0171", "SYM-0172", "SYM-0173", "SYM-0174", "SYM-0353", "SYM-0354",
  "SYM-0355", "SYM-0356", "SYM-0357", "SYM-0438", "SYM-0439",
];
const selected = newlyReviewedIds.map((id) => registry.find((item) => item.id === id));

assert.ok(selected.every(Boolean));
assert.ok(selected.every((item) => item.category === "Sensores y transductores"));
assert.ok(selected.every((item) => item.review_status === "engine_reviewed"));
assert.ok(selected.every((item) => item.kind !== "sensor_block"));
assert.deepEqual(Object.keys(selected.find((item) => item.id === "SYM-0163").ports), ["1", "2", "3", "4"]);
assert.deepEqual(Object.keys(selected.find((item) => item.id === "SYM-0167").ports), ["VCC", "GND", "SDA", "SCL"]);
assert.deepEqual(Object.keys(selected.find((item) => item.id === "SYM-0170").ports), ["IP+", "IP-", "VCC", "GND", "OUT"]);
assert.deepEqual(Object.keys(selected.find((item) => item.id === "SYM-0356").ports), ["E1", "E2", "VCC", "GND", "OUT"]);
assert.deepEqual(
  Object.keys(selected.find((item) => item.id === "SYM-0439").ports),
  ["IN+", "IN-", "VDD1", "GND1", "VDD2", "GND2", "OUT"],
);
selected.forEach((symbol) => {
  Object.entries(symbol.ports).forEach(([portName, port]) => {
    const onVerticalEdge = Math.abs(port.x) === symbol.width / 2;
    const onHorizontalEdge = Math.abs(port.y) === symbol.height / 2;
    assert.ok(onVerticalEdge || onHorizontalEdge, `${symbol.id}.${portName} is not on the symbol boundary`);
    assert.ok(Math.abs(port.x) <= symbol.width / 2, `${symbol.id}.${portName} exceeds symbol width`);
    assert.ok(Math.abs(port.y) <= symbol.height / 2, `${symbol.id}.${portName} exceeds symbol height`);
  });
});

const components = selected.map((symbol, index) => ({
  ref: `S${index + 1}`,
  display_ref: symbol.id,
  symbol_id: symbol.id,
  value: symbol.kind,
  position: { x: 10 + (index % 4) * 19, y: 10 + Math.floor(index / 4) * 17 },
}));
const nets = components.map((component, index) => ({
  id: `SENSOR${index + 1}`,
  show_label: false,
  connections: [`${component.ref}.${Object.keys(selected[index].ports)[0]}`],
}));
const result = core.render({
  schema_version: "1.0",
  document_kind: "circuit_diagram",
  standard_profile: "IEC_EXPERIMENTAL",
  title: "ElectroIA · sensores HVAC y medida revisados",
  document_id: "ELECTROIA-HVAC-SENSORS-REVIEW",
  revision: "A",
  components,
  nets,
});

assert.doesNotMatch(result.svg, /class="component review-auto_draft"/);
assert.equal(result.diagnostics.errors.length, 0);
newlyReviewedIds.forEach((id) => assert.match(result.svg, new RegExp(`data-symbol-id="${id}"`)));
assert.match(result.svg, />RTD</);
assert.match(result.svg, />CO₂</);
assert.match(result.svg, />H₂O</);
assert.match(result.svg, />SHUNT</);

await mkdir("test-artifacts", { recursive: true });
const browser = await chromium.launch({
  headless: true,
  executablePath: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  args: ["--disable-gpu", "--no-first-run"],
});
const page = await browser.newPage({ viewport: { width: 1900, height: 1600 }, deviceScaleFactor: 1 });
await page.setContent(`<style>body{margin:0;background:#e9ece9}svg{display:block;width:100%;height:auto}</style>${result.svg}`);
await page.screenshot({ path: "test-artifacts/electroia-hvac-sensors-reviewed.png", fullPage: true });
await browser.close();
process.stdout.write("ElectroIA HVAC sensors visual: 17 reviewed symbols OK\n");
