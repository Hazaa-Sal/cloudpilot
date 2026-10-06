// Run with: playwright-cli -s=cloudpilot run-code --filename=scripts/dashboard-smoke.js
// Open the local dashboard in that named session first. Creates one denied demo plan.
async page => {
  await page.unrouteAll({ behavior: 'ignoreErrors' });
  const check = (condition, message) => { if (!condition) throw new Error(message); };
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.reload();
  await page.waitForFunction(() => document.querySelector('#healthStatus').textContent.includes('Online'));
  await page.getByLabel('Application name', { exact: true }).fill('browser-smoke');
  await page.getByLabel('Environment', { exact: true }).selectOption('prod');
  await page.getByLabel('Replicas', { exact: true }).fill('1');
  await page.getByRole('button', { name: 'Generate infrastructure plan' }).click();
  await page.waitForFunction(() => document.querySelector('#policyBadge').textContent.includes('Denied'));
  check(await page.locator('#violations').textContent() === 'Production deployments require at least 2 replicas.', 'Policy result missing');
  check(await page.locator('#planView').evaluate(el => el === document.activeElement), 'Result focus missing');
  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Download plan JSON' }).click();
  const download = await downloadPromise;
  let data = '';
  for await (const chunk of await download.createReadStream()) data += chunk.toString();
  const plan = JSON.parse(data);
  check(plan.application === 'browser-smoke' && plan.status === 'denied', 'Incorrect exported plan');

  // Exercise paging without filling the user's persistent database with fixtures.
  const fixtures = Array.from({ length: 10 }, (_, index) => ({ ...plan,
    application: 'saved-' + index, plan_id: 'fixture-' + index,
  }));
  await page.route('**/api/v1/history?*', route => {
    const offset = Number(route.request().url().match(/[?&]offset=(\d+)/)[1]);
    return route.fulfill({ json: fixtures.slice(offset, offset + 9) });
  });
  await page.getByRole('button', { name: 'Refresh', exact: true }).click();
  await page.waitForFunction(() => document.querySelector('#historyPage').textContent === 'Plans 1–8');
  await page.getByRole('button', { name: 'Older →' }).click();
  await page.waitForFunction(() => document.querySelector('#historyPage').textContent === 'Plans 9–10');
  check(await page.locator('#olderHistory').isDisabled(), 'Last page allows older navigation');
  await page.locator('.history-row').first().focus();
  await page.keyboard.press('Enter');
  check(await page.locator('#planName').textContent() === 'saved-8', 'Keyboard history selection failed');
  await page.getByRole('button', { name: '← Newer' }).click();
  await page.waitForFunction(() => document.querySelector('#historyPage').textContent === 'Plans 1–8');

  await page.unroute('**/api/v1/history?*');
  await page.route('**/api/v1/history?*', route => route.fulfill({ status: 503, body: 'Unavailable' }));
  await page.getByRole('button', { name: 'Refresh', exact: true }).click();
  await page.waitForFunction(() => document.querySelector('#historyPage').textContent.includes('Refresh failed'));
  check(await page.locator('.history-row').count() === 8, 'Failed refresh discarded saved view');
  await page.route('**/api/v1/plans', route => route.fulfill({ status: 500, body: 'Internal Server Error' }));
  await page.getByRole('button', { name: 'Generate infrastructure plan' }).click();
  await page.locator('#errorBox.visible').waitFor();
  check((await page.locator('#errorBox').textContent()).includes('Please try again'), 'Unhelpful server error');
  check(await page.locator('#submitBtn').isEnabled(), 'Submit remains disabled after failure');
  await page.unroute('**/api/v1/plans');
  await page.unroute('**/api/v1/history?*');
  await page.route('**/api/v1/history?*', route => route.fulfill({ json: [] }));
  await page.getByRole('button', { name: 'Refresh', exact: true }).click();
  await page.waitForFunction(() => document.querySelector('#historyList').textContent.includes('No plans yet'));
  check(await page.locator('#olderHistory').isDisabled(), 'Empty history allows pagination');
  await page.unroute('**/api/v1/history?*');
  await page.route('**/health', route => route.fulfill({ status: 503, body: 'Unavailable' }));
  await page.reload();
  await page.waitForFunction(() => document.querySelector('#healthStatus').textContent.includes('Unreachable'));
  await page.unroute('**/health');
  await page.reload();
  await page.waitForFunction(() => document.querySelector('#healthStatus').textContent.includes('Online'));
  await page.setViewportSize({ width: 390, height: 844 });
  await page.locator('.history-row').first().click();
  check(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'Mobile horizontal overflow');
  await page.screenshot({ path: '.playwright-cli/cloudpilot-mobile.png', fullPage: true });
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.screenshot({ path: '.playwright-cli/cloudpilot-desktop.png', fullPage: true });
  check(errors.length === 0, 'Browser exceptions: ' + errors.join(', '));
  return 'PASS: real policy flow, JSON download, keyboard selection, pagination, HTTP errors, live health, mobile layout';
}
