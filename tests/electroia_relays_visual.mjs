import assert from "node:assert/strict";
import { mkdir } from "node:fs/promises";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const core = require("../archivo-tecnico-47097e44267b9cb111636b84823f1d47/diagram-core.js");

const ids = [
  "SYM-0107", "SYM-0108", "SYM-0109", "SYM-0113",
  "SYM-0114", "SYM-0115", "SYM-0116", "SYM-0118",
  "SYM-0122", "SYM-0124", "SYM-0125",
  "SYM-0425", "SYM-0426", "SYM-0427",
];
const positions = [
  { x: 10, y: 10 }, { x: 25, y: 10 }, { x: 42, y: 10 }, { x: 59, y: 10 },
  { x: 10, y: 24 }, { x: 25, y: 24 }, { x: 42, y: 24 }, { x: 59, y: 24 },
  { x: 11, y: 39 }, { x: 31, y: 39 }, { x: 49, y: 39 },
  { x: 11, y: 60 }, { x: 34, y: 60 }, { x: 59, y: 60 },
];
const registry = core.getRegistry().symbols;
const selected = ids.map((id) => registry.find((item) => item.id === id));
assert.ok(selected.every(Boolean));
assert.ok(selected.every((item) => item.review_status === "engine_reviewed"));
assert.equal(registry.filter((item) => item.category === "Relés, interruptores y actuadores").length, 23);
assert.ok(registry.filter((item) => item.category === "Relés, interruptores y actuadores").every((item) => item.review_status === "engine_reviewed"));
assert.deepEqual(Object.keys(selected[1].ports), ["COM", "NC", "NO"]);
assert.equal(Object.keys(selected[2].ports).length, 6);
assert.deepEqual(Object.keys(selected[8].ports), ["A1", "A2", "COM", "NC", "NO"]);
assert.equal(Object.keys(selected[13].ports).length, 14);

const components = selected.map((symbol, index) => ({
  ref: `K${index + 1}`,
  display_ref: symbol.id,
  symbol_id: symbol.id,
  value: symbol.kind,
  position: positions[index],
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
  title: "ElectroIA · relés, interruptores y actuadores revisados",
  document_id: "ELECTROIA-RELAYS-REVIEW",
  revision: "A",
  components,
  nets,
});
assert.doesNotMatch(result.svg, /class="component review-auto_draft"/);
assert.equal(result.diagnostics.errors.length, 0);

await mkdir("test-artifacts", { recursive: true });
const browser = await chromium.launch({
  headless: true,
  executablePath: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  args: ["--disable-gpu", "--no-first-run"],
});
const page = await browser.newPage({ viewport: { width: 1700, height: 1400 }, deviceScaleFactor: 1 });
await page.setContent(`<style>body{margin:0;background:#e9ece9}svg{display:block;width:100%;height:auto}</style>${result.svg}`);
await page.screenshot({ path: "test-artifacts/electroia-relays-reviewed.png", fullPage: true });
await browser.close();
process.stdout.write("ElectroIA relays visual: 14 new symbols and 23 reviewed family symbols OK\n");
