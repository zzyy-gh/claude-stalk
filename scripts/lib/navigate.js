// navigate.js — Feed navigation: Following tab click or list URL.

/**
 * Parse abbreviated numbers like "1.2K" or "150" to integers.
 */
function parseAbbreviatedNumber(str) {
  const m = str.match(/^([\d,.]+)\s*([KkMm]?)$/);
  if (!m) return null;
  const num = parseFloat(m[1].replace(/,/g, ''));
  const suffix = m[2].toUpperCase();
  if (suffix === 'K') return Math.round(num * 1000);
  if (suffix === 'M') return Math.round(num * 1000000);
  return Math.round(num);
}

/**
 * Navigate to the target feed.
 * @param {import('playwright').Page} page
 * @param {string} source - "following" or a list URL
 * @returns {{ listMembers: number | null }}
 */
export async function navigateToFeed(page, source) {
  if (source === 'following') {
    await page.goto('https://x.com/home', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(2000);

    // Click the "Following" tab
    const tab = page.locator('[role="tab"]').filter({ hasText: 'Following' });
    await tab.click({ timeout: 10000 });
    await page.waitForTimeout(2000);
    return { listMembers: null };
  } else {
    // List URL — navigate directly
    await page.goto(source, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(2000);

    // Check for error states
    const body = await page.textContent('body');
    if (body.includes("doesn't exist") || body.includes('Something went wrong')) {
      throw new Error(`List inaccessible: ${source}`);
    }

    // Extract list member count from page header
    let listMembers = null;
    const memberMatch = body.match(/([\d,.]+[KkMm]?)\s*[Mm]embers?/);
    if (memberMatch) {
      listMembers = parseAbbreviatedNumber(memberMatch[1].trim());
    }

    return { listMembers };
  }
}
