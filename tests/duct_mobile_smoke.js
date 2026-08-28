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
  assert.equal(await page.locator('[data-kind="machine-drag"]').count(), 1);
  assert.match(await page.locator('#heightConsistencyBadge').innerText(), /Altura única verificada: 25 cm/i);
  assert.equal(await page.locator('#heightConsistencyBadge.is-error').count(), 0);

  const machine = page.locator('[data-kind="machine-drag"]');
  const machineBefore = await machine.getAttribute('transform');
  await machine.scrollIntoViewIfNeeded();
  const machineBox = await machine.boundingBox();
  await page.mouse.move(machineBox.x + machineBox.width / 2, machineBox.y + machineBox.height / 2);
  await page.mouse.down();
  await page.mouse.move(machineBox.x + machineBox.width / 2 - 32, machineBox.y + machineBox.height / 2, {steps: 3});
  await page.mouse.up();
  const machineAfterDrag = await page.locator('[data-kind="machine-drag"]').getAttribute('transform');
  assert.notEqual(machineAfterDrag, machineBefore, 'El arrastre directo no movió la máquina.');
  await machine.click();
  await page.locator('#ductAdjustmentDock:visible').waitFor();
  assert.match(await page.locator('#ductAdjustmentTitle').innerText(), /Unidad interior/i);
  const machineBeforeButton = await page.locator('[data-kind="machine-drag"]').getAttribute('transform');
  await page.locator('[data-adjust-action="left"]').click();
  const machineAfter = await page.locator('[data-kind="machine-drag"]').getAttribute('transform');
  assert.notEqual(machineAfter, machineBeforeButton, 'Los botones grandes no movieron la máquina.');
  assert.match(await page.locator('#networkStatus').innerText(), /RED COMPLETA/i);
  await page.locator('#ductAdjustmentClose').click();

  const outlet = page.locator('[data-kind="outlet-drag"][data-id="bed-1"]');
  const before = await outlet.getAttribute('transform');
  await outlet.click();
  assert.equal(await page.locator('[data-kind="outlet-drag"][data-id="bed-1"].is-selected').count(), 1);
  assert.equal(await page.locator('[data-kind="outlet-wall-target"][data-id="bed-1"]').count(), 4);
  assert.match(await page.locator('#assistantMessage').innerText(), /Rejilla seleccionada/i);
  await page.locator('[data-adjust-action="wall-next"]').click();
  await page.locator('[data-adjust-action="wall-next"]').click();
  const after = await page.locator('[data-kind="outlet-drag"][data-id="bed-1"]').getAttribute('transform');
  assert.notEqual(after, before, 'Touch select-and-place did not move the grille.');
  const movedOutlet = page.locator('[data-kind="outlet-drag"][data-id="bed-1"]');
  assert.equal(await movedOutlet.getAttribute('data-centered'), 'true');
  assert.equal(await movedOutlet.getAttribute('data-wall-index'), '0');
  assert.equal(await movedOutlet.getAttribute('data-wall-angle'), '0');
  assert.match(after, /translate\(198 44\) rotate\(0\)/, 'The grille did not snap to the centre and direction of the selected wall.');
  assert.equal(await page.locator('[data-kind="outlet-drag"].is-selected').count(), 1);
  assert.match(await page.locator('#networkStatus').innerText(), /RED COMPLETA/i);

  await page.locator('[data-adjust-action="outlet-forward"]').click();
  assert.equal(await page.locator('[data-kind="outlet-drag"][data-id="bed-1"]').getAttribute('data-centered'), 'false');
  assert.equal(await page.locator('[data-kind="outlet-drag"][data-id="bed-1"]').getAttribute('data-wall-angle'), '0');
  await page.locator('#ductAdjustmentClose').click();

  const branchRoomId = await page.locator('g.branch-drag[data-kind="branch-drag"]').first().getAttribute('data-id');
  await page.locator(`g.branch-drag[data-kind="branch-drag"][data-id="${branchRoomId}"]`).first().click();
  await page.locator('#addAdjustmentGuide:visible').click();
  assert.equal(await page.locator(`g.branch-drag[data-kind="branch-drag"][data-id="${branchRoomId}"]`).count(), 2, 'No se añadió el segundo punto de paso del ramal.');
  await page.locator('[data-adjust-action="down"]').click();
  assert.match(await page.locator('#networkStatus').innerText(), /RED COMPLETA/i);
  await page.screenshot({path: 'test-artifacts/duct-mobile-adjustment-dock-v7.png', fullPage: false});
  await page.locator('#ductAdjustmentClose').click();

  const labelOverlapDetails = await page.evaluate(() => {
    const routes = [...document.querySelectorAll('.route-edge')].map(line => {
      const box = line.getBoundingClientRect();
      return { left: box.left - 8, right: box.right + 8, top: box.top - 8, bottom: box.bottom + 8 };
    });
    return [...document.querySelectorAll('.section-label > rect')].flatMap(rect => {
      const box = rect.getBoundingClientRect();
      return routes.filter(route => box.left < route.right && box.right > route.left && box.top < route.bottom && box.bottom > route.top).map(route => ({ label: rect.parentElement.dataset.sectionId, box: {left:box.left,right:box.right,top:box.top,bottom:box.bottom}, route }));
    });
  });
  assert.equal(labelOverlapDetails.length, 0, 'Una etiqueta de dimensiones sigue tapando un conducto.');

  const dimensions = await page.locator('#networkResults .result-row em').allTextContents();
  dimensions.forEach(value => {
    const match = value.match(/(\d+)\s*×\s*(\d+)/);
    assert.ok(match, `Missing duct dimensions in ${value}`);
    assert.equal(Number(match[1]) % 5, 0, `Duct width is not a 5 cm step: ${value}`);
    assert.equal(Number(match[2]), 25, `Duct height changed inside the same network: ${value}`);
  });

  assert.equal(await page.locator('.plan-frame.is-focus-mode').count(), 1);
  assert.equal(await page.locator('#planFocusToggle').getAttribute('aria-pressed'), 'true');
  await page.locator('#planFocusToggle').click();
  assert.equal(await page.locator('.plan-frame.is-focus-mode').count(), 0);
  await page.locator('#planFocusToggle').click();
  assert.equal(await page.locator('.plan-frame.is-focus-mode').count(), 1);
  await page.locator('#planFocusToggle').click();
  assert.equal(await page.locator('.plan-frame.is-focus-mode').count(), 0);
  await page.screenshot({path: 'test-artifacts/duct-mobile-adjustment-v7.png', fullPage: true});

  assert.equal(await page.locator('#saveDuctProject').isEnabled(), true);
  await page.locator('#saveDuctProject').click();
  assert.match(await page.locator('#assistantMessage').innerText(), /Guardado en/i);
  await page.goto(new URL('proyectos.html', base).href, {waitUntil: 'networkidle'});
  assert.equal(await page.locator('.project-row').count(), 1);
  assert.match(await page.locator('#artifactList').innerText(), /Conductos/i);
  assert.ok(await page.locator('#projectMeasurementRows tr').count() > 0);
  assert.match(await page.locator('#activeProjectName').innerText(), /Proyecto de campo/i);
  await page.screenshot({path: 'test-artifacts/projects-mobile-with-duct-v7.png', fullPage: true});

  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  assert.ok(overflow <= 1, `Mobile horizontal overflow: ${overflow}px`);
  assert.deepEqual(pageErrors, []);
  await browser.close();
  console.log('Duct mobile interaction smoke: OK');
})().catch(error => {
  console.error(error);
  process.exit(1);
});
