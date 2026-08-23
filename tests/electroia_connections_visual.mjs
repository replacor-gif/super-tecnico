import assert from "node:assert/strict";
import { mkdir } from "node:fs/promises";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const core = require("../archivo-tecnico-47097e44267b9cb111636b84823f1d47/diagram-core.js");
const selected = core.getRegistry().symbols.filter((item) => item.category === "Conexiones y referencias");
assert.equal(selected.length, 17);
assert.ok(selected.every((item) => item.review_status === "engine_reviewed"));

const components = selected.map((symbol, index) => ({
  ref: symbol.designator ? `${symbol.designator}${index + 1}` : `X${index + 1}`,
  display_ref: symbol.id,
  symbol_id: symbol.id,
  value: symbol.kind,
  position: { x: 7 + (index % 4) * 15, y: 7 + Math.floor(index / 4) * 13 },
}));
const nets = components.map((component, index) => {
  const firstPort = Object.keys(selected[index].ports)[0];
  if (selected[index].ports[firstPort].electrical_type === "no_connect") return null;
  return {
    id: `N${index + 1}`,
    show_label: false,
    connections: [`${component.ref}.${firstPort}`],
  };
}).filter(Boolean);
const result = core.render({
  schema_version: "1.0",
  document_kind: "circuit_diagram",
  standard_profile: "IEC_EXPERIMENTAL",
  title: "ElectroIA · conexiones y referencias revisadas",
  document_id: "ELECTROIA-CONNECTIONS-REVIEW",
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
const page = await browser.newPage({ viewport: { width: 1500, height: 1200 }, deviceScaleFactor: 1 });
await page.setContent(`<style>body{margin:0;background:#e9ece9}svg{display:block;width:100%;height:auto}</style>${result.svg}`);
await page.screenshot({ path: "test-artifacts/electroia-connections-reviewed.png", fullPage: true });
await browser.close();
process.stdout.write("ElectroIA connections visual: 17 reviewed symbols OK\n");
