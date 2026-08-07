'use strict';

const assert = require('node:assert/strict');
const {chromium} = require('playwright');

(async () => {
  const base = process.env.ST_TEST_URL || 'http://127.0.0.1:8765/componentes.html';
  const browser = await chromium.launch({
    headless: true,
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    args: ['--disable-gpu', '--no-first-run'],
  });
  const page = await browser.newPage({viewport: {width: 1365, height: 900}});
  await page.goto(base, {waitUntil: 'networkidle'});
  await page.locator('#componentQuery').fill('NE555');
  await page.locator('#componentSearchForm').evaluate(form => form.requestSubmit());
  await page.locator('.component-result').first().waitFor();
  assert.equal(await page.locator('.datasheet-finder:visible').count(), 0);
  await page.locator('.datasheet-option > summary').click();
  await page.locator('.datasheet-finder:visible').waitFor();
  const providers = await page.locator('.datasheet-source strong').allTextContents();
  for (const name of ['Mouser', 'DigiKey', 'Farnell', 'TME', 'Octopart', 'Google PDF']) {
    assert.ok(providers.includes(name), `Missing ${name}`);
  }
  assert.ok(await page.locator('.component-result').count() > 0);
  await page.screenshot({path: 'test-artifacts/components-datasheets-desktop.png', fullPage: true});

  await page.locator('#componentQuery').fill('REFERENCIA-NO-CATALOGADA-123');
  await page.locator('#componentSearchForm').evaluate(form => form.requestSubmit());
  await page.locator('.component-empty').waitFor();
  assert.equal(await page.locator('.component-result').count(), 0);
  assert.equal(await page.locator('.datasheet-finder:visible').count(), 0);
  await page.locator('.datasheet-option > summary').click();
  await page.locator('.datasheet-finder:visible').waitFor();
  assert.equal(await page.locator('.datasheet-source').count(), 6);

  await page.setViewportSize({width: 390, height: 844});
  await page.screenshot({path: 'test-artifacts/components-datasheets-mobile.png', fullPage: true});
  await browser.close();
  console.log('Components datasheet browser smoke: OK');
})().catch(error => {
  console.error(error);
  process.exit(1);
});
