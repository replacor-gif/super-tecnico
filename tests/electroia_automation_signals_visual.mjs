import assert from "node:assert/strict";
import { mkdir } from "node:fs/promises";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const core = require("../archivo-tecnico-47097e44267b9cb111636b84823f1d47/diagram-core.js");

const reviewedIds = [
  "SYM-0251", "SYM-0252", "SYM-0265", "SYM-0454", "SYM-0455",
  "SYM-0456", "SYM-0457", "SYM-0458", "SYM-0459", "SYM-0460",
];
const registry = core.getRegistry().symbols;
const selected = reviewedIds.map((id) => registry.find((item) => item.id === id));

assert.ok(selected.every(Boolean));
assert.ok(selected.every((item) => item.review_status === "engine_reviewed"));
assert.ok(selected.every((item) => !["connector_block", "digital_block", "generic_2p", "generic_4p"].includes(item.kind)));
assert.deepEqual(Object.keys(selected[0].ports), ["DI", "DE", "nRE", "RO", "A", "B", "VCC", "GND"]);
assert.deepEqual(Object.keys(selected[1].ports), ["TXD", "RXD", "CANH", "CANL", "VCC", "GND"]);
assert.deepEqual(Object.keys(selected[3].ports), ["LOOP+", "LOOP-"]);
assert.deepEqual(Object.keys(selected[9].ports), ["DA1", "DA2"]);

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
  ref: `IF${index + 1}`,
  display_ref: symbol.id,
  symbol_id: symbol.id,
  value: symbol.kind,
  position: { x: 11 + (index % 3) * 23, y: 11 + Math.floor(index / 3) * 19 },
}));
const nets = components.map((component, index) => ({
  id: `INTERFACE${index + 1}`,
  show_label: false,
  connections: [`${component.ref}.${Object.keys(selected[index].ports)[0]}`],
}));
const result = core.render({
  schema_version: "1.0",
  document_kind: "circuit_diagram",
  standard_profile: "IEC_EXPERIMENTAL",
  title: "ElectroIA · señales y comunicaciones industriales revisadas",
  document_id: "ELECTROIA-AUTOMATION-SIGNALS-REVIEW",
  revision: "A",
  components,
  nets,
});

assert.doesNotMatch(result.svg, /class="component review-auto_draft"/);
assert.equal(result.diagnostics.errors.length, 0);
reviewedIds.forEach((id) => assert.match(result.svg, new RegExp(`data-symbol-id="${id}"`)));
for (const text of ["RS-485", "CAN", "ETH", "4–20 mA", "0–10 V", "UART", "JTAG / SWD", "MODBUS", "BACnet", "DALI"]) {
  assert.ok(result.svg.includes(`>${text}<`), text);
}

await mkdir("test-artifacts", { recursive: true });
const browser = await chromium.launch({
  headless: true,
  executablePath: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  args: ["--disable-gpu", "--no-first-run"],
});
const page = await browser.newPage({ viewport: { width: 1800, height: 1500 }, deviceScaleFactor: 1 });
await page.setContent(`<style>body{margin:0;background:#e9ece9}svg{display:block;width:100%;height:auto}</style>${result.svg}`);
await page.screenshot({ path: "test-artifacts/electroia-automation-signals-reviewed.png", fullPage: true });
await browser.close();
process.stdout.write("ElectroIA automation signals visual: 10 reviewed symbols OK\n");
