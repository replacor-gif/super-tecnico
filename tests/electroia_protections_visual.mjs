import assert from "node:assert/strict";
import { mkdir } from "node:fs/promises";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const core = require("../archivo-tecnico-47097e44267b9cb111636b84823f1d47/diagram-core.js");
const selected = core.getRegistry().symbols.filter((item) => item.category === "Protecciones eléctricas");
assert.equal(selected.length, 16);
assert.ok(selected.every((item) => item.review_status === "engine_reviewed"));

const components = selected.map((symbol, index) => ({
  ref: symbol.designator ? `${symbol.designator.replace(/[^A-Z]/gi, "") || "P"}${index + 1}` : `P${index + 1}`,
  display_ref: symbol.id,
  symbol_id: symbol.id,
  value: symbol.kind,
  position: { x: 8 + (index % 4) * 16, y: 8 + Math.floor(index / 4) * 14 },
}));
const nets = components.map((component, index) => ({
  id: `P${index + 1}`,
  show_label: false,
  connections: [`${component.ref}.${Object.keys(selected[index].ports)[0]}`],
}));
const result = core.render({
  schema_version: "1.0",
  document_kind: "circuit_diagram",
  standard_profile: "IEC_EXPERIMENTAL",
  title: "ElectroIA · protecciones eléctricas revisadas",
  document_id: "ELECTROIA-PROTECTIONS-REVIEW",
  revision: "A",
  components,
  nets,
});
assert.doesNotMatch(result.svg, /class="component review-auto_draft"/);

await mkdir("test-artifacts", { recursive: true });
const browser = await chromium.launch({
  headless: true,
  executablePath: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  args: ["--disable-gpu", "--no-first-run"],
});
const page = await browser.newPage({ viewport: { width: 1500, height: 1100 }, deviceScaleFactor: 1 });
await page.setContent(`<style>body{margin:0;background:#e9ece9}svg{display:block;width:100%;height:auto}</style>${result.svg}`);
await page.screenshot({ path: "test-artifacts/electroia-protections-reviewed.png", fullPage: true });
await browser.close();
process.stdout.write("ElectroIA protections visual: 16 reviewed symbols OK\n");
