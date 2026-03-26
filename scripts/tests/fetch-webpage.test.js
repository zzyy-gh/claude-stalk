// Test: scripts/fetch-webpage.js argument validation
// Run: node scripts/tests/fetch-webpage.test.js

import { execFileSync } from 'node:child_process';
import { strict as assert } from 'node:assert';

const cwd = 'C:/Users/zzyy/Desktop/claude-stalk';
let passed = 0;

// Test: missing --url exits with error
try {
  execFileSync('node', ['scripts/fetch-webpage.js', '--text-output', '/tmp/test.md'], {
    cwd, encoding: 'utf-8', stdio: ['pipe', 'pipe', 'pipe'],
  });
  assert.fail('should have thrown');
} catch (e) {
  assert.ok(e.status !== 0, 'should exit non-zero');
  assert.ok(e.stderr.includes('--url is required'), `expected --url error, got: ${e.stderr}`);
  passed++;
  console.log('  PASS  missing --url exits with error');
}

// Test: missing --text-output exits with error
try {
  execFileSync('node', ['scripts/fetch-webpage.js', '--url', 'https://example.com'], {
    cwd, encoding: 'utf-8', stdio: ['pipe', 'pipe', 'pipe'],
  });
  assert.fail('should have thrown');
} catch (e) {
  assert.ok(e.status !== 0, 'should exit non-zero');
  assert.ok(e.stderr.includes('--text-output is required'), `expected --text-output error, got: ${e.stderr}`);
  passed++;
  console.log('  PASS  missing --text-output exits with error');
}

// Test: no args at all exits with error
try {
  execFileSync('node', ['scripts/fetch-webpage.js'], {
    cwd, encoding: 'utf-8', stdio: ['pipe', 'pipe', 'pipe'],
  });
  assert.fail('should have thrown');
} catch (e) {
  assert.ok(e.status !== 0, 'should exit non-zero');
  passed++;
  console.log('  PASS  no args exits with error');
}

console.log(`\nfetch-webpage.js: ${passed} passed`);
