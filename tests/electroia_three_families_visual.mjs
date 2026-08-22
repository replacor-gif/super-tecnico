import assert from "node:assert/strict";
import { mkdir } from "node:fs/promises";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const core = require("../archivo-tecnico-47097e44267b9cb111636b84823f1d47/diagram-core.js");
const expected = new Map([
  ["Componentes pasivos", 34],
  ["Semiconductores discretos", 43],
  ["Optoelectrónica y aislamiento", 10],
]);
const registry = core.getRegistry().symbols;
const selected = registry.filter((symbol) => expected.has(symbol.category));

for (const [category, count] of expected) {
  const family = selected.filter((symbol) => symbol.category === category);
  assert.equal(family.length, count, category);
  assert.ok(family.every((symbol) => symbol.review_status === "engine_reviewed"), `${category} mantiene borradores`);
  assert.ok(family.every((symbol) => symbol.geometry_source === "reviewed_seed"), `${category} no usa semilla revisada`);
  assert.ok(family.every((symbol) => Object.keys(symbol.ports).length >= 2), `${category} tiene símbolos sin terminales`);
}

const columns = 6;
const components = selected.map((symbol, index) => ({
  ref: `X${index + 1}`,
  display_ref: symbol.id,
  symbol_id: symbol.id,
  value: symbol.name,
  position: {x: 9 + (index % columns) * 17, y: 8 + Math.floor(index / columns) * 13},
}));
const nets = components.map((component, index) => ({id: `N${index + 1}`, show_label: false, connections: [`${component.ref}.${Object.keys(selected[index].ports)[0]}`]}));
const result = core.render({schema_version:"1.0", document_kind:"circuit_diagram", standard_profile:"IEC_EXPERIMENTAL", title:"ElectroIA · tres familias normalizadas", document_id:"ELECTROIA-THREE-FAMILY-REVIEW", revision:"A", components, nets});
assert.doesNotMatch(result.svg, /class="component review-auto_draft"/);

await mkdir("test-artifacts", {recursive:true});
const browser = await chromium.launch({headless:true, executablePath:"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe", args:["--disable-gpu", "--no-first-run"]});
const page = await browser.newPage({viewport:{width:1900, height:1500}, deviceScaleFactor:1});
await page.setContent(`<style>body{margin:0;background:#e9ece9}svg{display:block;width:100%;height:auto}</style>${result.svg}`);
await page.screenshot({path:"test-artifacts/electroia-three-families-reviewed.png", fullPage:true});
await browser.close();
process.stdout.write(`ElectroIA three-family visual: ${selected.length} reviewed symbols OK\n`);
