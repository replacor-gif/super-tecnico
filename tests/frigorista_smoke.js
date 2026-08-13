'use strict';

const assert = require('node:assert/strict');
const {chromium} = require('playwright');

(async () => {
  const base = process.env.ST_TEST_URL || 'http://127.0.0.1:8765/frigorista.html';
  const browser = await chromium.launch({
    headless: true,
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    args: ['--disable-gpu', '--no-first-run'],
  });
  const page = await browser.newPage({viewport: {width: 390, height: 844}, deviceScaleFactor: 1});
  const pageErrors = [];
  page.on('pageerror', error => pageErrors.push(error.message));
  await page.goto(base, {waitUntil: 'networkidle'});

  await page.locator('#catalogStatus').filter({hasText: '56 refrigerantes'}).waitFor();
  await page.locator('[data-refrigerant="R407C"]').click();
  await page.locator('#pressureInput').fill('5');
  await page.locator('#ptForm').evaluate(form => form.requestSubmit());
  await page.locator('#resultPanel:visible').waitFor();
  assert.equal(await page.locator('#blendResult:visible').count(), 1);
  assert.match(await page.locator('#resultExplanation').innerText(), /rocío/i);
  assert.ok(parseFloat((await page.locator('#glideValue').innerText()).replace(',', '.')) > 3);

  await page.locator('#lineTemperatureButton').click();
  await page.locator('#measurementInput').fill('10');
  await page.locator('#measurementForm').evaluate(form => form.requestSubmit());
  await page.locator('#analysisPanel:visible').waitFor();
  assert.match(await page.locator('#derivedSummary').innerText(), /Recalentamiento/i);
  assert.equal(await page.locator('#nextMeasurementButton').getAttribute('data-measurement'), 'high_pressure');

  await page.locator('#nextMeasurementButton').click();
  assert.equal(await page.locator('input[name="side"]:checked').getAttribute('value'), 'condensation');
  await page.locator('#pressureInput').fill('18');
  await page.locator('#ptForm').evaluate(form => form.requestSubmit());
  await page.locator('#lineTemperatureButton').click();
  await page.locator('#measurementInput').fill('36');
  await page.locator('#measurementForm').evaluate(form => form.requestSubmit());
  assert.match(await page.locator('#derivedSummary').innerText(), /Subenfriamiento/i);
  assert.equal(await page.locator('#nextMeasurementButton').getAttribute('data-measurement'), 'discharge_line_temperature');
  await page.locator('#nextMeasurementButton').click();
  await page.locator('#measurementInput').fill('82');
  await page.locator('#measurementForm').evaluate(form => form.requestSubmit());
  await page.locator('#mollierContent:visible').waitFor();
  assert.match(await page.locator('#mollierStatus').innerText(), /CICLO COMPLETO/i);
  assert.equal(await page.locator('#mollierChart .fr-chart-point').count(), 4);
  assert.match(await page.locator('#mollierPerformance').innerText(), /COP DEL CICLO/i);
  await page.screenshot({path: 'test-artifacts/frigorista-mollier-mobile.png', fullPage: true});

  await page.locator('#newQueryButton').click();
  await page.locator('[data-refrigerant="R32"]').click();
  await page.locator('#pressureInput').fill('7');
  await page.locator('.fr-segmented label').filter({hasText: 'Evaporación'}).click();
  await page.locator('#ptForm').evaluate(form => form.requestSubmit());
  assert.equal(await page.locator('#singleResult:visible').count(), 1);

  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  assert.ok(overflow <= 1, `Mobile horizontal overflow: ${overflow}px`);
  assert.deepEqual(pageErrors, []);
  await page.screenshot({path: 'test-artifacts/frigorista-mobile.png', fullPage: true});

  await page.setViewportSize({width: 1365, height: 900});
  await page.screenshot({path: 'test-artifacts/frigorista-desktop.png', fullPage: true});
  await browser.close();
  console.log('Frigorista browser smoke: OK');
})().catch(error => {
  console.error(error);
  process.exit(1);
});
