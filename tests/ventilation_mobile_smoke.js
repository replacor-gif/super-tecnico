'use strict';

const assert = require('node:assert/strict');
const { chromium } = require('playwright');

(async () => {
  const base = process.env.ST_TEST_URL || 'http://127.0.0.1:8766/ventilacion.html';
  const browser = await chromium.launch({
    headless: true,
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    args: ['--disable-gpu', '--no-first-run'],
  });
  const page = await browser.newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1, hasTouch: true });
  const pageErrors = [];
  page.on('pageerror', error => pageErrors.push(error.message));
  await page.goto(base, { waitUntil: 'networkidle' });
  await page.evaluate(() => localStorage.clear());
  await page.reload({ waitUntil: 'networkidle' });

  assert.equal(await page.locator('#ventProfile').inputValue(), 'cte_dwelling');
  assert.equal(await page.locator('#ventDefaultHeight').inputValue(), '2.5');
  await page.locator('#ventLoadExample').click();
  await page.locator('#ventAutomaticResult:visible').waitFor();
  assert.match(await page.locator('#ventNetworkStatus').innerText(), /RED CALCULADA/i);
  assert.equal(await page.locator('[data-kind="vent-terminal"]').count(), 5);
  assert.equal(await page.locator('[data-kind="vent-fan"]').count(), 2);
  assert.ok(await page.locator('.vent-route.route-supply').count() > 0);
  assert.ok(await page.locator('.vent-route.route-extract').count() > 0);
  assert.ok(await page.locator('#ventNetworkResults .result-row').count() > 0);
  assert.doesNotMatch(await page.locator('#ventFanResults').innerText(), /recorrido m[aá]s largo 0[,\.]0 m/i);
  assert.match(await page.locator('#ventResultSummary').innerText(), /72 m³\/h/);
  assert.match(await page.locator('#ventResultSummary').innerText(), /86 m³\/h/);

  await page.locator('[data-place-tool="delete"]').click();
  await page.locator('[data-kind="vent-terminal"][data-id="sup-main"]').click({ force: true });
  assert.equal(await page.locator('[data-kind="vent-terminal"]').count(), 4);
  assert.match(await page.locator('#ventNetworkStatus').innerText(), /FALTA COMPLETAR/i);

  await page.locator('[data-place-tool="terminal-supply"]').click();
  const svg = page.locator('#ventPlanStage svg');
  const box = await svg.boundingBox();
  assert.ok(box);
  await svg.click({ position: { x: box.width * .17, y: box.height * .22 }, force: true });
  assert.equal(await page.locator('[data-kind="vent-terminal"]').count(), 5);
  assert.match(await page.locator('#ventNetworkStatus').innerText(), /RED CALCULADA/i);

  await page.locator('[data-place-tool="terminal-supply"]').click();
  const extractFan = page.locator('[data-kind="vent-fan"][data-id="fan-extract"]');
  const fanBefore = await extractFan.getAttribute('transform');
  await extractFan.click({ force: true });
  assert.equal(await page.locator('[data-kind="vent-fan"][data-id="fan-extract"].is-selected').count(), 1);
  assert.match(await page.locator('#ventAssistantMessage').innerText(), /Turbina seleccionada/i);
  await svg.click({ position: { x: box.width * .71, y: box.height * .53 }, force: true });
  const fanAfter = await page.locator('[data-kind="vent-fan"][data-id="fan-extract"]').getAttribute('transform');
  assert.notEqual(fanAfter, fanBefore, 'Touch select-and-place did not move the fan.');
  assert.match(await page.locator('#ventNetworkStatus').innerText(), /RED CALCULADA/i);

  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  assert.ok(overflow <= 1, `Mobile horizontal overflow: ${overflow}px`);
  assert.deepEqual(pageErrors, []);
  await page.screenshot({ path: 'test-artifacts/ventilation-mobile.png', fullPage: true });

  const desktop = await browser.newPage({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 1 });
  const desktopErrors = [];
  desktop.on('pageerror', error => desktopErrors.push(error.message));
  await desktop.goto(base, { waitUntil: 'networkidle' });
  await desktop.locator('#ventLoadExample').click();
  await desktop.locator('#ventAutomaticResult:visible').waitFor();
  assert.match(await desktop.locator('#ventNetworkStatus').innerText(), /RED CALCULADA/i);
  const desktopOverflow = await desktop.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  assert.ok(desktopOverflow <= 1, `Desktop horizontal overflow: ${desktopOverflow}px`);
  assert.deepEqual(desktopErrors, []);
  await desktop.screenshot({ path: 'test-artifacts/ventilation-desktop.png', fullPage: true });
  await browser.close();
  console.log('Ventilation mobile and desktop placement/routing smoke: OK');
})().catch(error => {
  console.error(error);
  process.exit(1);
});
