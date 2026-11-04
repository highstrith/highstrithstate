import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { test } from 'node:test';

const root = path.resolve(import.meta.dirname, '..');

test('Pages push trigger uses the branch permitted by the production environment', () => {
  const workflow = fs.readFileSync(path.join(root, '.github/workflows/pages.yml'), 'utf8');
  const push = workflow.match(/^  push:\r?\n    branches: \[([^\]]+)\]/m);
  assert.ok(push, 'Pages push trigger must declare its publishing branch');
  const branches = [...push[1].matchAll(/["']([^"']+)["']/g)].map(match => match[1]);
  assert.deepEqual(branches, ['main'], 'github-pages permits main; a release-only push cannot publish');
});

test('Pages Prepare site packages the real local CSS and JavaScript references', () => {
  const workflow = fs.readFileSync(path.join(root, '.github/workflows/pages.yml'), 'utf8');
  const step = workflow.match(/^      - name: Prepare site\r?\n        run: \|\r?\n((?:          [^\r\n]*(?:\r?\n|$)|\r?\n)*)/m);
  assert.ok(step, 'workflow must contain the actual Prepare site shell block');
  const script = step[1].replace(/^ {10}/gm, '');
  const source = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
  const projects = fs.readFileSync(path.join(root, 'projects.html'), 'utf8');
  const progress = fs.readFileSync(path.join(root, 'in-progress.html'), 'utf8');
  const resume = fs.readFileSync(path.join(root, 'resume.html'), 'utf8');
  // 橘生梦厂已独立成站：reel/ 不再进作品集产物，首页入口必须是绝对地址外链。
  const standaloneEntry = 'https://highstrith.github.io/jusheng/';
  const externalEntries = [...source.matchAll(/href="(https:\/\/highstrith\.github\.io\/jusheng\/)"/g)].length;
  assert.ok(externalEntries >= 4, `index must link the standalone site (${standaloneEntry}) from the entry link and all three cards`);
  assert.equal((source.match(/href="reel\//g) || []).length, 0, 'index must not link the retired /reel/ path');
  const recommendationCovers = [...new Set([...source.matchAll(/src="(assets\/film-recommendation\/[^"]+)"/g)].map((match) => match[1]))];
  assert.equal(recommendationCovers.length, 3, 'index must reference three local film-recommendation covers');
  const references = [...(source + projects + progress + resume).matchAll(/<(?:link|script)\b[^>]*>/gi)].flatMap(([tag]) => {
    const attribute = /^<script\b/i.test(tag) ? 'src' : /\brel=["']stylesheet["']/i.test(tag) ? 'href' : null;
    const reference = attribute && tag.match(new RegExp(`\\b${attribute}=["']([^"']+)["']`, 'i'))?.[1];
    if (!reference) return [];
    const url = new URL(reference, 'https://pages.fixture/');
    return url.origin === 'https://pages.fixture' ? [decodeURIComponent(url.pathname.slice(1))] : [];
  });
  assert.ok(references.length > 0, 'real index must reference local CSS or JavaScript');
  const projectFiles = [...(projects + progress + resume).matchAll(/(?:href|src)="(assets\/[^"]+)"/g)].map(match => match[1].split('?')[0]);
  const fixture = fs.mkdtempSync(path.join(os.tmpdir(), 'highstrith-pages-'));
  try {
    for (const file of ['index.html', 'projects.html', 'in-progress.html', 'resume.html', 'admin.html', 'admin.css', 'serve.js']) {
      if (fs.existsSync(path.join(root, file))) {
        fs.copyFileSync(path.join(root, file), path.join(fixture, file));
      }
    }
    for (const folder of ['assets', 'data']) fs.mkdirSync(path.join(fixture, folder));
    for (const file of [...references, ...projectFiles]) {
      fs.mkdirSync(path.join(fixture, path.dirname(file)), { recursive: true });
      fs.copyFileSync(path.join(root, file), path.join(fixture, file));
    }
    fs.copyFileSync(path.join(root, 'assets/studio-mark.svg'), path.join(fixture, 'assets/studio-mark.svg'));
    for (const cover of recommendationCovers) {
      fs.mkdirSync(path.join(fixture, path.dirname(cover)), { recursive: true });
      fs.copyFileSync(path.join(root, cover), path.join(fixture, cover));
    }
    // The real repository always has an uploads folder; the fixture only copies
    // referenced files, so recreate it or the uploads rsync step has no source.
    fs.mkdirSync(path.join(fixture, 'assets/uploads'), { recursive: true });
    fs.copyFileSync(path.join(root, 'data/works.json'), path.join(fixture, 'data/works.json'));
    execFileSync('/bin/bash', ['-e', '-o', 'pipefail', '-c', script], { cwd: fixture, stdio: 'pipe' });

    const publicRoot = path.join(fixture, 'public');
    const html = fs.readFileSync(path.join(publicRoot, 'index.html'), 'utf8');
    assert.equal(html, source);
    assert.equal(fs.readFileSync(path.join(publicRoot, 'projects.html'), 'utf8'), projects);
    assert.equal(fs.readFileSync(path.join(publicRoot, 'in-progress.html'), 'utf8'), progress);
    assert.equal(fs.readFileSync(path.join(publicRoot, 'resume.html'), 'utf8'), resume);
    assert.deepEqual(fs.readFileSync(path.join(publicRoot, 'assets/lin-junjie-resume.pdf')), fs.readFileSync(path.join(root, 'assets/lin-junjie-resume.pdf')));
    // 橘生梦厂在独立仓库发布：作品集产物里的 /reel/ 只允许留一张跳转页，防止双发布。
    const reelDir = path.join(publicRoot, 'reel');
    assert.deepEqual(fs.readdirSync(reelDir), ['index.html'], 'reel/ may only keep a redirect stub, the site itself ships from highstrith/jusheng');
    const stub = fs.readFileSync(path.join(reelDir, 'index.html'), 'utf8');
    assert.match(stub, /http-equiv="refresh"[^>]*jusheng/, 'the old /reel/ address must redirect to the standalone site');
    assert.match(stub, /rel="canonical" href="https:\/\/highstrith\.github\.io\/jusheng\/"/, 'the stub must point search engines at the new canonical URL');
    for (const cover of recommendationCovers) {
      assert.ok(fs.existsSync(path.join(publicRoot, cover)), `recommendation cover ${cover} must be published`);
    }
    assert.equal(fs.existsSync(path.join(publicRoot, 'server')), false, 'review server must stay outside the static artifact');
    assert.deepEqual(references.filter(file => !fs.existsSync(path.join(publicRoot, file))), [], 'Pages artifact is missing local CSS/JS referenced by index.html');
    for (const file of [...references, ...projectFiles, 'assets/studio-mark.svg', 'data/works.json']) {
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
