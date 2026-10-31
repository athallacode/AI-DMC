import {createRequire} from 'node:module';
import assert from 'node:assert/strict';
import path from 'node:path';
const require = createRequire(import.meta.url);
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
if (!process.env.QA_PASSWORD) throw new Error('Set QA_PASSWORD for isolated QA backend.');
const browser = await chromium.launch({headless:true,channel:'chrome'});
const page = await browser.newPage({viewport:{width:375,height:812}});
try {
  await page.goto(`${process.env.QA_FRONTEND_URL || 'http://localhost:3000'}/login`);
  await page.getByLabel('Username',{exact:true}).fill(process.env.QA_USERNAME || 'dosen1');
  await page.getByLabel('Password',{exact:true}).fill(process.env.QA_PASSWORD);
  await page.getByRole('button',{name:'Masuk',exact:true}).click();
  await page.waitForURL('**/unggah');
  await page.locator('.mobile-nav').getByRole('link',{name:/Verifikasi/}).click();
  const trigger = page.locator('.verification-card').first().getByRole('button',{name:'Koreksi',exact:true});
  await trigger.waitFor(); await trigger.click();
  const dialog = page.getByRole('dialog',{name:'Koreksi dokumen'});
  await dialog.getByRole('button',{name:'Simpan dan setujui',exact:true}).waitFor({state:'visible'});
  await page.waitForTimeout(300);
  for (let i=0;i<30;i++) {
    await page.keyboard.press('Tab');
    assert.equal(await page.evaluate(() => !!document.activeElement?.closest('[role=dialog]')),true,'Tab focus remains in modal');
  }
  for (let i=0;i<30;i++) {
    await page.keyboard.press('Shift+Tab');
    assert.equal(await page.evaluate(() => !!document.activeElement?.closest('[role=dialog]')),true,'Shift+Tab focus remains in modal');
  }
  await dialog.getByLabel('Judul',{exact:false}).fill('Dokumen hasil koreksi QA');
  await dialog.evaluate(element => element.scrollTo(0,0));
  await page.waitForTimeout(250);
  await page.screenshot({path:path.resolve('../docs/screenshots/koreksi-mobile.png'),fullPage:false});
  await page.keyboard.press('Escape'); await dialog.waitFor({state:'detached'});
  assert.equal(await trigger.evaluate(element => element === document.activeElement),true,'Esc restores focus to original trigger');
  console.log(JSON.stringify({passed:true,checks:['30 Tab cycles','30 Shift+Tab cycles','Esc closes','focus returns','final mobile modal screenshot']}));
} finally {await browser.close();}
