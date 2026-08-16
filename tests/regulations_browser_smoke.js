'use strict';

const assert = require('node:assert/strict');
const {chromium} = require('playwright');

(async () => {
  const base = process.env.ST_TEST_URL || 'http://127.0.0.1:8765/normativa.html';
  const browser = await chromium.launch({
    headless: true,
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    args: ['--disable-gpu', '--no-first-run'],
  });
  const page = await browser.newPage({viewport: {width: 390, height: 844}, deviceScaleFactor: 1});
  const pageErrors = [];
  page.on('pageerror', error => pageErrors.push(error.message));
  await page.goto(`${base}?doc=rebt&q=que%20seccion%20debe%20tener%20un%20cable%20en%20una%20vivienda`, {waitUntil: 'networkidle'});

  await page.locator('.rg-result-card').first().waitFor();
  assert.equal(await page.locator('.rg-refinement.is-required').count(), 1);
  assert.match(await page.locator('.rg-result-card').first().innerText(), /ITC-BT-25/i);
  assert.match(await page.locator('.rg-result-card').first().innerText(), /PÁGINA 169/i);

  await page.locator('[data-refine="alumbrado"]').click();
  await page.locator('.rg-refinement.is-required').waitFor({state: 'detached'});
  await page.locator('.rg-result-card').first().filter({hasText: 'PÁGINA 169'}).waitFor();
  const firstResult = await page.locator('.rg-result-card').first().innerText();
  assert.match(firstResult, /ITC-BT-25/i);
  assert.match(firstResult, /Tabla 1/i);
  assert.match(firstResult, /TABLA/i);
  assert.equal(await page.locator('.rg-refinement.is-required').count(), 0);

  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  assert.ok(overflow <= 1, `Mobile horizontal overflow: ${overflow}px`);
  assert.deepEqual(pageErrors, []);
  await page.screenshot({path: 'test-artifacts/regulations-structured-mobile.png', fullPage: true});

  await page.setViewportSize({width: 1365, height: 900});
  await page.screenshot({path: 'test-artifacts/regulations-structured-desktop.png', fullPage: true});
  await browser.close();
  console.log('Regulations structured browser smoke: OK');
})().catch(error => {
  console.error(error);
  process.exit(1);
});
