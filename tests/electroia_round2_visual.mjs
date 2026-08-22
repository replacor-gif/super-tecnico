import assert from "node:assert/strict";
import { mkdir } from "node:fs/promises";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const core = require("../archivo-tecnico-47097e44267b9cb111636b84823f1d47/diagram-core.js");
const expected = new Map([
  ["Circuitos integrados funcionales", 50],
  ["Electrónica digital", 73],
  ["Potencia y climatización", 66],
]);
const registry = core.getRegistry().symbols;
for (const [category, count] of expected) {
  const family = registry.filter((symbol) => symbol.category === category);
  assert.equal(family.length, count, category);
  assert.ok(family.every((symbol) => symbol.review_status === "engine_reviewed"), `${category} mantiene borradores`);
  assert.ok(family.every((symbol) => Object.keys(symbol.ports).length >= 2), `${category} tiene símbolos sin terminales`);
}

const selectedIds = [
  "SYM-0183", "SYM-0193", "SYM-0198", "SYM-0205",
  "SYM-0212", "SYM-0224", "SYM-0242", "SYM-0254",
  "SYM-0268", "SYM-0270", "SYM-0278", "SYM-0399",
];
const selected = selectedIds.map((id) => registry.find((symbol) => symbol.id === id));
assert.ok(selected.every(Boolean));
const components = selected.map((symbol, index) => ({
  ref: `X${index + 1}`,
  display_ref: symbol.id,
  symbol_id: symbol.id,
  value: symbol.name,
  position: {x: 10 + (index % 4) * 22, y: 10 + Math.floor(index / 4) * 17},
}));
const nets = components.map((component, index) => ({id: `N${index + 1}`, show_label: false, connections: [`${component.ref}.${Object.keys(selected[index].ports)[0]}`]}));
const result = core.render({schema_version:"1.0", document_kind:"circuit_diagram", standard_profile:"IEC_EXPERIMENTAL", title:"ElectroIA · normalización masiva 2", document_id:"ELECTROIA-ROUND2-REVIEW", revision:"A", components, nets});
assert.doesNotMatch(result.svg, /class="component review-auto_draft"/);
assert.match(result.svg, />&amp;<\/text>/);
assert.match(result.svg, />ƒ<\/text>/);
assert.match(result.svg, />W<\/text>/);

await mkdir("test-artifacts", {recursive:true});
const browser = await chromium.launch({headless:true, executablePath:"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe", args:["--disable-gpu", "--no-first-run"]});
const page = await browser.newPage({viewport:{width:1600, height:980}, deviceScaleFactor:1});
await page.setContent(`<style>body{margin:0;background:#e9ece9}svg{display:block;width:100%;height:auto}</style>${result.svg}`);
await page.screenshot({path:"test-artifacts/electroia-round2-reviewed.png", fullPage:true});
await browser.close();
process.stdout.write(`ElectroIA round-two visual: ${[...expected.values()].reduce((a,b)=>a+b,0)} reviewed symbols OK\n`);
