import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { test } from 'node:test';

const root = path.resolve(import.meta.dirname, '..');

test('Pages Prepare site packages the real local CSS and JavaScript references', () => {
  const workflow = fs.readFileSync(path.join(root, '.github/workflows/pages.yml'), 'utf8');
  const step = workflow.match(/^      - name: Prepare site\r?\n        run: \|\r?\n((?:          [^\r\n]*(?:\r?\n|$)|\r?\n)*)/m);
  assert.ok(step, 'workflow must contain the actual Prepare site shell block');
  const script = step[1].replace(/^ {10}/gm, '');
  const fixture = fs.mkdtempSync(path.join(os.tmpdir(), 'highstrith-pages-'));
  try {
    for (const file of ['index.html', 'admin.html', 'admin.css', 'serve.js']) {
      fs.copyFileSync(path.join(root, file), path.join(fixture, file));
    }
    for (const folder of ['assets', 'data']) fs.mkdirSync(path.join(fixture, folder));
    for (const file of ['studio.css', 'studio.js']) {
      fs.copyFileSync(path.join(root, 'assets', file), path.join(fixture, 'assets', file));
    }
    fs.copyFileSync(path.join(root, 'assets/studio-mark.svg'), path.join(fixture, 'assets/studio-mark.svg'));
    fs.copyFileSync(path.join(root, 'data/works.json'), path.join(fixture, 'data/works.json'));
    execFileSync('/bin/bash', ['-e', '-o', 'pipefail', '-c', script], { cwd: fixture, stdio: 'pipe' });

    const publicRoot = path.join(fixture, 'public');
    const html = fs.readFileSync(path.join(publicRoot, 'index.html'), 'utf8');
    assert.equal(html, fs.readFileSync(path.join(root, 'index.html'), 'utf8'));
    const references = [...html.matchAll(/<(?:link|script)\b[^>]*>/gi)].flatMap(([tag]) => {
      const attribute = /^<script\b/i.test(tag) ? 'src' : /\brel=["']stylesheet["']/i.test(tag) ? 'href' : null;
      const reference = attribute && tag.match(new RegExp(`\\b${attribute}=["']([^"']+)["']`, 'i'))?.[1];
      if (!reference) return [];
      const url = new URL(reference, 'https://pages.fixture/');
      return url.origin === 'https://pages.fixture' ? [decodeURIComponent(url.pathname.slice(1))] : [];
    });
    assert.ok(references.length > 0, 'real index must reference local CSS or JavaScript');
    assert.deepEqual(references.filter(file => !fs.existsSync(path.join(publicRoot, file))), [], 'Pages artifact is missing local CSS/JS referenced by index.html');
    for (const file of [...references, 'assets/studio-mark.svg', 'data/works.json']) {
      assert.deepEqual(fs.readFileSync(path.join(publicRoot, file)), fs.readFileSync(path.join(root, file)), `${file} must be copied unchanged`);
    }
    assert.ok(fs.existsSync(path.join(publicRoot, '.nojekyll')));
    for (const file of ['admin.html', 'admin.css', 'serve.js']) {
      assert.equal(fs.existsSync(path.join(publicRoot, file)), false, `${file} must stay outside the public artifact`);
    }
  } finally {
    fs.rmSync(fixture, { recursive: true, force: true });
  }
});
