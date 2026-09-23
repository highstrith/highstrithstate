import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(import.meta.dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const works = JSON.parse(fs.readFileSync(path.join(root, 'data/works.json'), 'utf8'));
const media = [
  'assets/hero-digital-human.jpg',
  'assets/works/prove-it.mp4',
  'assets/works/approach.mp4',
  'assets/works/giant-wheel.mp4',
  'assets/works/exported-film.mp4',
  'assets/works/timeline-vertical.mp4',
];
const posters = [
  'assets/posters/prove-it.jpg',
  'assets/posters/approach.jpg',
  'assets/posters/giant-wheel.jpg',
  'assets/posters/exported-film.jpg',
  'assets/posters/timeline-vertical.jpg',
];

for (const asset of [...media, ...posters]) {
  assert.ok(fs.existsSync(path.join(root, asset)), `missing media asset: ${asset}`);
  assert.match(html, new RegExp(asset.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')), `index.html must reference ${asset}`);
}

assert.match(html, /const baseWorkData = \[\s*[\s\S]*?\];/);
assert.equal((html.match(/assets\/works\//g) || []).length, 5, 'five starter works must be configured');
assert.equal(works.length, 7, 'all seven portfolio works must be editable from the catalog');
assert.equal(new Set(works.map((work) => work.id)).size, works.length, 'catalog work ids must be unique');
assert.ok(works.every((work) => work.cnTitle && work.enTitle && work.cnSub && work.enSub && work.cnDesc && work.enDesc), 'catalog works must include titles, categories, and descriptions');
for (const work of works) {
  assert.ok(fs.existsSync(path.join(root, work.video)), `missing video for ${work.cnTitle}: ${work.video}`);
  if (work.mobileVideo) {
    assert.ok(fs.existsSync(path.join(root, work.mobileVideo)), `missing mobile video for ${work.cnTitle}: ${work.mobileVideo}`);
  }
}
