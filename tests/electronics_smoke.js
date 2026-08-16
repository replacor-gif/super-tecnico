'use strict';

const { chromium } = require('playwright');
const assert = require('node:assert/strict');

(async () => {
  const base = process.env.ST_TEST_URL || 'http://127.0.0.1:8765/electronica-placas.html';
  const browser = await chromium.launch({headless:true, executablePath:'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', args:['--disable-gpu','--no-first-run']});
  const page = await browser.newPage({viewport:{width:1440,height:1000},deviceScaleFactor:1});
  await page.route('**/api/index.php?action=page-view', route => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ok:true, views:123}),
  }));
  await page.route('**/api/index.php?action=page-rating*', route => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ok:true, likes:12, dislikes:1, user_vote:null}),
  }));
  page.setDefaultTimeout(5000);
  page.setDefaultNavigationTimeout(10000);
  const errors = [];
  page.on('console', message => { if (message.type() === 'error') errors.push(`${message.text()} · ${message.location().url || 'sin URL'}`); });
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(base, {waitUntil:'networkidle'});
  console.log('loaded');

  assert.equal(await page.locator('#elModuleCount').textContent(), '23');
  assert.equal(await page.locator('#elModuleGrid .el-module-card').count(), 23);
  assert.ok((await page.locator('#elModuleGrid .el-module-card h3').first().textContent()).includes('Resistencias'));
  assert.equal(await page.locator('.el-group-card').count(), 11);
  assert.equal(await page.locator('#elToolLinks .el-tool-card').count(), 5);
  await page.screenshot({path:'test-artifacts/electronics-home.png', fullPage:true});

  await page.locator('[data-view="lookup"]').click();
  await page.locator('#elSearch').fill('ULN2003');
  await page.locator('#elSearchForm button').click();
  console.log('searched');
  assert.ok(await page.locator('#elResultsList .el-result').count() > 0);
  await page.locator('#elResultsList .el-result').first().click();
  console.log('reader');
  assert.equal(await page.locator('#elReader').isVisible(), true);
  assert.ok((await page.locator('#elChapterContent').innerText()).length > 80);
  assert.ok(await page.locator('#elChapterSelect option').count() > 10);
  await page.screenshot({path:'test-artifacts/electronics-desktop.png'});
  console.log('desktop screenshot');

  await page.locator('#elReaderBack').click();
  await page.locator('[data-view="library"]').click();
  assert.equal(await page.locator('#elModuleGrid .el-module-card').count(), 23);
  console.log('library');
  await page.locator('#elGroupFilter').selectOption('potencia');
  assert.ok(await page.locator('#elModuleGrid .el-module-card').count() >= 4);

  await page.evaluate(() => localStorage.setItem('st.language','en'));
  await page.reload({waitUntil:'networkidle'});
  assert.equal(await page.locator('[data-el-i18n="libraryTab"]').textContent(), 'Encyclopedia by topic');
  console.log('translation');

  await page.setViewportSize({width:390,height:844});
  await page.locator('[data-view="groups"]').click();
  assert.equal(await page.locator('.el-group-card').count(), 11);
  await page.screenshot({path:'test-artifacts/electronics-mobile.png'});
  console.log('mobile screenshot');
  assert.deepEqual(errors, []);
  await browser.close();
  console.log('electronics smoke test: OK');
})().catch(error => { console.error(error); process.exit(1); });
