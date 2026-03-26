#!/usr/bin/env node
// fetch-webpage.js — Playwright-based webpage fetcher with readability extraction.
// Uses same chromium/session setup as scrape-x.js.
//
// Usage:
//   node scripts/fetch-webpage.js --url "https://example.com/post" --html-output raw.html --text-output article.md
//   node scripts/fetch-webpage.js --url "https://example.com/post" --text-output article.md  (skip raw HTML)

import { chromium } from 'playwright';
import { parseArgs } from 'node:util';
import { writeFileSync } from 'node:fs';
import { resolve, join } from 'node:path';
import { homedir } from 'node:os';
import { Readability } from '@mozilla/readability';
import { JSDOM } from 'jsdom';

// --- CLI args ---

const { values: args } = parseArgs({
  options: {
    url:           { type: 'string' },
    'html-output': { type: 'string' },
    'text-output': { type: 'string' },
    'session-dir': { type: 'string', default: join(homedir(), 'playwright-session-claude-stalk') },
    timeout:       { type: 'string', default: '30000' },
  },
  strict: true,
});

const url = args.url;
const htmlOutput = args['html-output'] ? resolve(args['html-output']) : null;
const textOutput = args['text-output'] ? resolve(args['text-output']) : null;
const sessionDir = args['session-dir'];
const timeout = Number(args.timeout);

if (!url) {
  process.stderr.write('Error: --url is required\n');
  process.exit(1);
}
if (!textOutput) {
  process.stderr.write('Error: --text-output is required\n');
  process.exit(1);
}

// --- Main ---

async function main() {
  let context;
  try {
    context = await chromium.launchPersistentContext(sessionDir, {
      headless: true,
      args: ['--disable-blink-features=AutomationControlled'],
      viewport: { width: 1280, height: 900 },
    });

    const page = await context.newPage();

    process.stderr.write(`Fetching: ${url}\n`);
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout });

    // Wait a bit for dynamic content to settle
    await page.waitForTimeout(2000);

    // Get raw HTML
    const rawHtml = await page.content();

    // Save raw HTML if requested
    if (htmlOutput) {
      writeFileSync(htmlOutput, rawHtml, 'utf-8');
      process.stderr.write(`Raw HTML saved: ${htmlOutput}\n`);
    }

    // Extract readable text via Readability
    const dom = new JSDOM(rawHtml, { url });
    const reader = new Readability(dom.window.document);
    const article = reader.parse();

    if (!article || !article.textContent || article.textContent.trim().length < 50) {
      process.stderr.write('Warning: Readability extraction returned minimal content\n');
      // Fallback: extract body text directly
      const bodyText = await page.evaluate(() => {
        const body = document.body;
        if (!body) return '';
        // Remove scripts, styles, nav, footer, header
        const remove = body.querySelectorAll('script, style, nav, footer, header, aside, [role="navigation"], [role="banner"], [role="contentinfo"]');
        remove.forEach(el => el.remove());
        return body.innerText || '';
      });

      const markdown = `# ${article?.title || url}\n\n${bodyText.trim()}`;
      writeFileSync(textOutput, markdown, 'utf-8');
      process.stderr.write(`Fallback text saved: ${textOutput} (${bodyText.trim().split(/\s+/).length} words)\n`);
    } else {
      // Convert to markdown-ish format
      const title = article.title || url;
      const markdown = `# ${title}\n\n${article.textContent.trim()}`;
      writeFileSync(textOutput, markdown, 'utf-8');
      process.stderr.write(`Text saved: ${textOutput} (${article.textContent.trim().split(/\s+/).length} words)\n`);
    }

    // Output metadata as JSON to stdout
    const metadata = {
      title: article?.title || null,
      byline: article?.byline || null,
      siteName: article?.siteName || null,
      excerpt: article?.excerpt || null,
      wordCount: article?.textContent?.trim().split(/\s+/).length || 0,
      url: page.url(),  // Final URL after redirects
    };
    process.stdout.write(JSON.stringify(metadata) + '\n');

    await page.close();
  } catch (err) {
    process.stderr.write(`Error: ${err.message}\n`);
    process.exit(2);
  } finally {
    if (context) {
      await context.close();
    }
  }
}

main();
