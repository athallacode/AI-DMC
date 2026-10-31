// Read-only UI checks against an isolated mock QA backend. Login writes its normal audit record.
import { createRequire } from 'node:module';
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';

const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
if (!process.env.QA_PASSWORD) throw new Error('Set QA_PASSWORD for the isolated QA accounts.');
const base = process.env.QA_FRONTEND_URL || 'http://localhost:3000';
const output = path.resolve('../docs/screenshots/v2');
await fs.mkdir(output, { recursive: true });
const browser = await chromium.launch({ headless: true, channel: 'chrome' });
const report = { pages: [], font: [], keyboard: [], errors: [] };

async function login(username) {
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await context.newPage();
  page.on('pageerror', e => report.errors.push(e.message));
  await page.goto(`${base}/login`);
  await page.getByLabel('Username', { exact: true }).fill(username);
  await page.getByLabel('Password', { exact: true }).fill(process.env.QA_PASSWORD);
  await page.getByRole('button', { name: 'Masuk', exact: true }).click();
  await page.waitForURL('**/unggah');
  await page.locator('.demo-pill').waitFor();
  return { context, page };
}

async function typography(page, selector) {
  return page.locator(selector).first().evaluate(el => {
    const s = getComputedStyle(el);
    return { family: s.fontFamily, size: s.fontSize, weight: s.fontWeight, tracking: s.letterSpacing, lineHeight: s.lineHeight, color: s.color };
  });
}

async function renderedFont(page) {
  const client = await page.context().newCDPSession(page);
  await client.send('DOM.enable');
  await client.send('CSS.enable');
  const { root } = await client.send('DOM.getDocument');
  for (const selector of ['h1', '.page-heading p']) {
    const { nodeId } = await client.send('DOM.querySelector', { nodeId: root.nodeId, selector });
    const { fonts } = await client.send('CSS.getPlatformFontsForNode', { nodeId });
    assert(fonts.length && fonts.every(f => /Inter/i.test(f.familyName) && f.isCustomFont), JSON.stringify(fonts));
    report.font.push({ selector, fonts });
  }
  await client.detach();
  assert.equal(await page.locator('body').evaluate(el => getComputedStyle(el).webkitFontSmoothing), 'antialiased');
  assert((await page.locator('body').evaluate(el => getComputedStyle(el).fontFeatureSettings)).includes('"cv11"'));
}

async function capture(page, route, width, name) {
  await page.setViewportSize({ width, height: 900 });
  await page.goto(`${base}${route}`);
  await page.locator('h1').waitFor();
  await page.locator('.demo-pill').waitFor();
  await page.waitForFunction(() => !/Memuat|Memeriksa sesi/.test(document.querySelector('main')?.innerText || ''));
  await page.evaluate(() => document.fonts.ready);
  const layout = await page.evaluate(() => ({ width: innerWidth, scrollWidth: document.documentElement.scrollWidth, banner: !!document.querySelector('main > .demo-notice') }));
  assert.equal(layout.scrollWidth, width, `${name}: page overflow`);
  assert.equal(layout.banner, false);
  const h1 = await typography(page, 'h1');
  assert.equal(h1.size, width === 375 ? '34px' : '44px');
  assert.equal(h1.weight, '700');
  assert(Math.abs(parseFloat(h1.tracking) - (width === 375 ? -1.02 : -1.32)) < .01);
  const subtitle = await typography(page, '.page-heading p');
  assert.equal(subtitle.size, '17px');
  if (route === '/arsip') {
    assert.equal(await page.locator('.filter-fields select').count(), 2);
    for (const select of await page.locator('.filter-fields select').all()) {
      assert.equal(await select.evaluate(el => getComputedStyle(el).appearance), 'none');
    }
    assert.equal(await page.locator('.category-filter').evaluate(el => el.scrollWidth > el.clientWidth), false);
    assert(!/\[MOCK\]/i.test(await page.locator('.archive').innerText()));
    if (width === 1280 && await page.locator('.archive tbody tr').count()) {
      assert.equal(await page.locator('.archive tbody tr').first().evaluate(el => el.getBoundingClientRect().height), 56);
    }
  }
  if (route === '/unggah') {
    const dropzone = page.locator('.dropzone');
    const idle = await dropzone.evaluate(el => ({ border: getComputedStyle(el).borderStyle, outline: getComputedStyle(el).outlineStyle }));
    assert.notEqual(idle.border, 'dashed');
    assert.notEqual(idle.outline, 'dashed');
    await dropzone.dispatchEvent('dragover');
    assert.equal(await dropzone.evaluate(el => getComputedStyle(el).outlineStyle), 'dashed');
    await dropzone.dispatchEvent('dragleave');
    assert.equal(await page.locator('.dropzone .app-icon').evaluate(el => el.getBoundingClientRect().width), 56);
    if (await page.locator('.recent-row').count()) {
      assert.equal(await page.locator('.recent-row').first().evaluate(el => el.getBoundingClientRect().height), 64);
    }
    assert.equal(await page.locator('.camera-button').isVisible(), width === 375);
  }
  await page.screenshot({ path: path.join(output, `${name}-${width}.png`), fullPage: width === 1280 });
  report.pages.push({ page: name, ...layout, h1, subtitle });
}

try {
  const populated = await login(process.env.QA_USERNAME || 'dosen1');
  for (const width of [1280, 375]) {
    await capture(populated.page, '/unggah', width, 'unggah');
    await capture(populated.page, '/arsip', width, 'arsip');
  }
  await renderedFont(populated.page);
  const avatar = populated.page.locator('.account summary');
  await avatar.focus();
  assert.equal(await avatar.evaluate(el => getComputedStyle(el).outlineStyle), 'solid');
  await populated.page.keyboard.press('Enter');
  assert.equal(await populated.page.locator('.account').evaluate(el => el.open), true);
  await populated.page.keyboard.press('Tab');
  await populated.page.keyboard.press('Escape');
  assert.equal(await populated.page.locator('.account').evaluate(el => el.open), false);
  assert.equal(await avatar.evaluate(el => el === document.activeElement), true);
  report.keyboard.push('Avatar Enter opens; Escape closes and returns focus; visible focus ring');

  const empty = await login(process.env.QA_EMPTY_USERNAME || 'dosen2');
  for (const width of [1280, 375]) {
    await capture(empty.page, '/verifikasi', width, 'verifikasi');
    const state = empty.page.getByRole('heading', { name: 'Semua sudah dicek', exact: true });
    await state.waitFor();
    assert.equal(await state.evaluate(el => !!el.closest('.card')), false);
  }
  // Render a pending state using read-only browser interception. No document is
  // uploaded, approved or edited in the backend for these visual checks.
  const backend = process.env.QA_BACKEND_URL || 'http://localhost:8000';
  const authToken = await populated.page.evaluate(() => sessionStorage.getItem('ai-dmc-token'));
  const headers = { Authorization: `Bearer ${authToken}` };
  const summaries = await (await fetch(`${backend}/documents`, { headers })).json();
  const source = summaries.find(doc => doc.nama_berkas === 'high.png');
  assert(source, 'Dedicated QA database needs the existing synthetic high.png fixture.');
  const fixture = await (await fetch(`${backend}/documents/${source.id}`, { headers })).json();
  fixture.status = 'menunggu_verifikasi';
  fixture.skor_keyakinan = .72;
  await populated.context.route(`${backend}/documents**`, async route => {
    const url = new URL(route.request().url());
    if (route.request().method() === 'GET' && url.pathname === '/documents' && url.searchParams.get('status') === 'menunggu_verifikasi') {
      await route.fulfill({ json: [fixture] });
    } else if (route.request().method() === 'GET' && url.pathname === `/documents/${fixture.id}`) {
      await route.fulfill({ json: fixture });
    } else { await route.continue(); }
  });
  report.verificationCardSource = 'Browser-only pending-state fixture; existing synthetic high.png; no backend document mutation';
  await populated.page.goto(`${base}/verifikasi`);
  await populated.page.locator('h1').waitFor();
  await populated.page.waitForFunction(() => !/Memuat dokumen/.test(document.querySelector('main')?.innerText || ''));
  if (await populated.page.locator('.verification-card').count()) {
    const trigger = populated.page.locator('.verification-card').first().getByRole('button', { name: 'Koreksi', exact: true });
    await trigger.click();
    const dialog = populated.page.getByRole('dialog', { name: 'Koreksi dokumen' });
    await dialog.locator('.select-wrap select').first().waitFor();
    for (const key of ['Tab', 'Shift+Tab']) {
      for (let i = 0; i < 25; i++) {
        await populated.page.keyboard.press(key);
        assert.equal(await populated.page.evaluate(() => !!document.activeElement?.closest('[role=dialog]')), true);
      }
    }
    await populated.page.keyboard.press('Escape');
    await dialog.waitFor({ state: 'detached' });
    assert.equal(await trigger.evaluate(el => el === document.activeElement), true);
    report.keyboard.push('Correction modal 25 Tab/25 Shift+Tab cycles; Escape and focus restoration');
    for (const width of [1280, 375]) {
      await populated.page.setViewportSize({ width, height: 900 });
      await populated.page.locator('.preview').first().locator('iframe, img, .empty').waitFor();
      await populated.page.screenshot({ path: path.join(output, `verifikasi-terisi-${width}.png`), fullPage: true });
    }
  }
  assert.equal(report.errors.length, 0);
  report.passed = true;
  await fs.writeFile(path.join(output, 'checks.json'), JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report));
} finally { await browser.close(); }
