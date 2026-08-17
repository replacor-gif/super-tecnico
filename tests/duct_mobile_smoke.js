'use strict';

const assert = require('node:assert/strict');
const {chromium} = require('playwright');

(async () => {
  const base = process.env.ST_TEST_URL || 'http://127.0.0.1:8765/conductos.html';
  const browser = await chromium.launch({
    headless: true,
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    args: ['--disable-gpu', '--no-first-run'],
  });
  const page = await browser.newPage({viewport: {width: 390, height: 844}, deviceScaleFactor: 1, hasTouch: true});
  const pageErrors = [];
  page.on('pageerror', error => pageErrors.push(error.message));
  await page.goto(base, {waitUntil: 'networkidle'});
  await page.evaluate(() => localStorage.clear());
  await page.reload({waitUntil: 'networkidle'});

  await page.locator('#loadExample').click();
  await page.locator('#automaticResult:visible').waitFor();
  assert.match(await page.locator('#networkStatus').innerText(), /RED COMPLETA/i);
  assert.ok(await page.locator('[data-kind="outlet-drag"]').count() >= 3);
  assert.ok(await page.locator('[data-kind="branch-drag"]').count() >= 1);

  const outlet = page.locator('[data-kind="outlet-drag"][data-id="bed-1"]');
  const before = await outlet.getAttribute('transform');
  await outlet.click();
  assert.equal(await page.locator('[data-kind="outlet-drag"][data-id="bed-1"].is-selected').count(), 1);
  assert.equal(await page.locator('[data-kind="outlet-wall-target"][data-id="bed-1"]').count(), 4);
  assert.match(await page.locator('#assistantMessage').innerText(), /Rejilla seleccionada/i);
  await page.locator('[data-kind="outlet-wall-target"][data-id="bed-1"][data-wall-index="0"]').click({force: true});
  const after = await page.locator('[data-kind="outlet-drag"][data-id="bed-1"]').getAttribute('transform');
  assert.notEqual(after, before, 'Touch select-and-place did not move the grille.');
  const movedOutlet = page.locator('[data-kind="outlet-drag"][data-id="bed-1"]');
  assert.equal(await movedOutlet.getAttribute('data-centered'), 'true');
  assert.equal(await movedOutlet.getAttribute('data-wall-index'), '0');
  assert.equal(await movedOutlet.getAttribute('data-wall-angle'), '0');
  assert.match(after, /translate\(198 44\) rotate\(0\)/, 'The grille did not snap to the centre and direction of the selected wall.');
  assert.equal(await page.locator('[data-kind="outlet-drag"].is-selected').count(), 0);
  assert.match(await page.locator('#networkStatus').innerText(), /RED COMPLETA/i);

  const dimensions = await page.locator('#networkResults .result-row em').allTextContents();
  dimensions.forEach(value => {
    const match = value.match(/(\d+)\s*×\s*(\d+)/);
    assert.ok(match, `Missing duct dimensions in ${value}`);
    assert.equal(Number(match[1]) % 5, 0, `Duct width is not a 5 cm step: ${value}`);
  });
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  assert.ok(overflow <= 1, `Mobile horizontal overflow: ${overflow}px`);
  assert.deepEqual(pageErrors, []);
  await page.screenshot({path: 'test-artifacts/duct-mobile-adjustment.png', fullPage: true});
  await browser.close();
  console.log('Duct mobile interaction smoke: OK');
})().catch(error => {
  console.error(error);
  process.exit(1);
});
