import { mkdir } from "node:fs/promises";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const core = require("../archivo-tecnico-47097e44267b9cb111636b84823f1d47/diagram-core.js");
const families = [
  "generic_1p", "generic_2p", "generic_3p", "generic_4p",
  "connector_block", "digital_block", "functional_block", "sensor_block",
  "semiconductor_block", "machine_block", "protection_block", "power_block",
  "isolation_block", "installation_block", "meter_block", "source_block",
];
const registry = core.getRegistry().symbols;
const selected = families.map((kind) => registry.find((item) => item.kind === kind)).filter(Boolean);
const components = selected.map((symbol, index) => ({
  ref: `X${index + 1}`,
  symbol_id: symbol.id,
  value: symbol.kind,
  position: { x: 7 + (index % 4) * 14, y: 7 + Math.floor(index / 4) * 12 },
}));
const nets = components.map((component, index) => {
  const symbol = selected[index];
  return {
    id: `N${index + 1}`,
    show_label: false,
    connections: [`${component.ref}.${Object.keys(symbol.ports)[0]}`],
  };
});
const result = core.render({
  schema_version: "1.0",
  document_kind: "circuit_diagram",
  standard_profile: "IEC_EXPERIMENTAL",
  title: "ElectroIA · familias provisionales normalizadas",
  document_id: "ELECTROIA-FAMILY-PREVIEW",
  revision: "A",
  components,
  nets,
});

await mkdir("test-artifacts", { recursive: true });
const browser = await chromium.launch({
  headless: true,
  executablePath: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  args: ["--disable-gpu", "--no-first-run"],
});
const page = await browser.newPage({ viewport: { width: 1500, height: 1100 }, deviceScaleFactor: 1 });
await page.setContent(`<style>body{margin:0;background:#e9ece9}svg{display:block;width:100%;height:auto}</style>${result.svg}`);
await page.screenshot({ path: "test-artifacts/electroia-symbol-families.png", fullPage: true });
await browser.close();
process.stdout.write(`ElectroIA symbol family visual: ${selected.length} families OK\n`);
