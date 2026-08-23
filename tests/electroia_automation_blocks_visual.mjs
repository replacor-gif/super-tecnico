import assert from 'node:assert/strict';
import { mkdir } from 'node:fs/promises';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const core = require('../archivo-tecnico-47097e44267b9cb111636b84823f1d47/diagram-core.js');

const ids = [
  'SYM-0461', 'SYM-0463', 'SYM-0464', 'SYM-0465', 'SYM-0466',
  'SYM-0467', 'SYM-0462', 'SYM-0468', 'SYM-0469', 'SYM-0470', 'SYM-0471',
];
const symbols = core.getRegistry().symbols;
const selected = ids.map(id => symbols.find(symbol => symbol.id === id));
assert.ok(selected.every(Boolean));
assert.ok(selected.every(symbol => symbol.review_status === 'engine_reviewed'));
selected.forEach(symbol => Object.entries(symbol.ports).forEach(([name, port]) => {
  assert.ok(Math.abs(port.x) === symbol.width / 2 || Math.abs(port.y) === symbol.height / 2, `${symbol.id}.${name} is not on the shared 50 mil grid boundary`);
}));

const components = selected.map((symbol, index) => ({
  ref: `A${index + 1}`,
  display_ref: symbol.designator,
  symbol_id: symbol.id,
  value: symbol.name,
  position: { x: 12 + (index % 4) * 22, y: 12 + Math.floor(index / 4) * 24 },
}));
const nets = components.map((component, index) => ({ id: `AUTO${index + 1}`, show_label: false, connections: [`${component.ref}.${Object.keys(selected[index].ports)[0]}`] }));
const rendered = core.render({
  schema_version: '1.0', document_kind: 'circuit_diagram', standard_profile: 'IEC_EXPERIMENTAL',
  title: 'ElectroIA · automatización industrial normalizada', document_id: 'ELECTROIA-AUTOMATION-BLOCKS', revision: 'A', components, nets,
});
assert.equal(rendered.diagnostics.errors.length, 0);
assert.doesNotMatch(rendered.svg, /class="component review-auto_draft"/);
for (const id of ids) assert.match(rendered.svg, new RegExp(`data-symbol-id="${id}"`));
for (const label of ['PLC CPU', 'DI', 'DO', 'AI', 'AO', 'REMOTE I/O', 'SAFETY PLC', 'HMI', '24 V DC', 'ETH SWITCH', 'GATEWAY']) assert.ok(rendered.svg.includes(`>${label}<`), label);

await mkdir('test-artifacts', { recursive: true });
const browser = await chromium.launch({ headless: true, executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', args: ['--disable-gpu', '--no-first-run'] });
const page = await browser.newPage({ viewport: { width: 1900, height: 1300 }, deviceScaleFactor: 1 });
await page.setContent(`<style>body{margin:0;background:#e9ece9}svg{display:block;width:100%;height:auto}</style>${rendered.svg}`);
await page.screenshot({ path: 'test-artifacts/electroia-automation-blocks-reviewed.png', fullPage: true });
await browser.close();
process.stdout.write('ElectroIA automation blocks visual: 11 public reviewed symbols OK\n');
