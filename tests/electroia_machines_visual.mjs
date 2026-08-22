import assert from "node:assert/strict";
import { mkdir } from "node:fs/promises";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const core = require("../archivo-tecnico-47097e44267b9cb111636b84823f1d47/diagram-core.js");

const registryResult = core.getRegistry();
assert.equal(registryResult.version, "0.9");
assert.equal(registryResult.engine_version, "1.10.0-alpha.1");
const registry = registryResult.symbols;
const selected = registry.filter((item) => item.category === "Máquinas y actuadores");
const newlyReviewedIds = [
  "SYM-0149", "SYM-0152", "SYM-0153", "SYM-0154", "SYM-0155", "SYM-0158", "SYM-0159",
  "SYM-0160", "SYM-0161", "SYM-0162", "SYM-0442", "SYM-0443", "SYM-0444", "SYM-0445",
];

assert.equal(selected.length, 18);
assert.ok(selected.every((item) => item.review_status === "engine_reviewed"));
assert.ok(newlyReviewedIds.every((id) => selected.some((item) => item.id === id)));
assert.ok(newlyReviewedIds.every((id) => selected.find((item) => item.id === id)?.kind !== "machine_block"));
assert.deepEqual(Object.keys(selected.find((item) => item.id === "SYM-0153").ports), ["A+", "A-", "B+", "B-"]);
assert.deepEqual(Object.keys(selected.find((item) => item.id === "SYM-0154").ports), ["A1", "AC", "A2", "B1", "BC", "B2"]);
assert.deepEqual(Object.keys(selected.find((item) => item.id === "SYM-0160").ports), ["A+", "A-", "B+", "B-"]);
assert.deepEqual(Object.keys(selected.find((item) => item.id === "SYM-0445").ports), ["C", "R", "S"]);
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
  ref: `M${index + 1}`,
  display_ref: symbol.id,
  symbol_id: symbol.id,
  value: symbol.kind,
  position: { x: 10 + (index % 4) * 18, y: 10 + Math.floor(index / 4) * 16 },
}));
const nets = components.map((component, index) => ({
  id: `MACHINE${index + 1}`,
  show_label: false,
  connections: [`${component.ref}.${Object.keys(selected[index].ports)[0]}`],
}));
const result = core.render({
  schema_version: "1.0",
  document_kind: "circuit_diagram",
  standard_profile: "IEC_EXPERIMENTAL",
  title: "ElectroIA · máquinas y actuadores revisados",
  document_id: "ELECTROIA-MACHINES-REVIEW",
  revision: "A",
  components,
  nets,
});

assert.doesNotMatch(result.svg, /class="component review-auto_draft"/);
assert.equal(result.diagnostics.errors.length, 0);
newlyReviewedIds.forEach((id) => assert.match(result.svg, new RegExp(`data-symbol-id="${id}"`)));
assert.match(result.svg, />BLDC</);
assert.match(result.svg, />PSC</);
assert.match(result.svg, />COMP</);

await mkdir("test-artifacts", { recursive: true });
const browser = await chromium.launch({
  headless: true,
  executablePath: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  args: ["--disable-gpu", "--no-first-run"],
});
const page = await browser.newPage({ viewport: { width: 1900, height: 1600 }, deviceScaleFactor: 1 });
await page.setContent(`<style>body{margin:0;background:#e9ece9}svg{display:block;width:100%;height:auto}</style>${result.svg}`);
await page.screenshot({ path: "test-artifacts/electroia-machines-reviewed.png", fullPage: true });
await browser.close();
process.stdout.write("ElectroIA machines visual: 14 new symbols and 18 reviewed family symbols OK\n");
