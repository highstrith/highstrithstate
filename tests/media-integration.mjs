import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';

const root = path.resolve(import.meta.dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const works = JSON.parse(fs.readFileSync(path.join(root, 'data/works.json'), 'utf8'));
const media = [
  'assets/hero-digital-human-full.jpg',
  'assets/hero-studio-red.jpg',
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

assert.ok(fs.statSync(path.join(root, 'assets/hero-studio-red.jpg')).size < 500_000, 'hero background should stay below 500 KB for mobile');
assert.doesNotMatch(html, /<link[^>]+rel="preload"[^>]+hero-studio-red/i, 'decorative hero background should not be preloaded');

assert.equal(works.length, 15, 'catalogue data retains all works, including hidden legacy entries');
const lyingDownFilm = works.find((work) => work.id === 'work-lying-down-20261001');
assert.equal(lyingDownFilm?.cnTitle, '趴着办公早该知道');
assert.equal(lyingDownFilm?.video, 'assets/uploads/lying-down-20261001.mp4');
assert.equal(lyingDownFilm?.poster, 'assets/uploads/posters/lying-down-20261001-16x9.png');
assert.match(html, /work-lying-down-20261001/, 'offline catalog must include the new film');
assert.ok(fs.existsSync(path.join(root, lyingDownFilm.poster)), 'the new film cover must exist');

const resetDay = works.find((work) => work.id === 'work-reset-day-20261007');
assert.equal(resetDay?.cnTitle, '重置日');
assert.equal(resetDay?.video, 'assets/uploads/reset-day-20261007.mp4');
assert.equal(resetDay?.poster, 'assets/uploads/posters/reset-day-20261007-16x9.png');
assert.match(html, /work-reset-day-20261007/, 'offline catalog must include 重置日');
assert.ok(fs.existsSync(path.join(root, resetDay.poster)), '重置日封面 must exist');
assert.deepEqual(works.map((work) => work.id).slice(0, 3), [
  'work-reset-day-20261007', 'work-lying-down-20261001', 'work-1783863606674-7ta9sp',
], 'catalogue must be ordered newest first');
assert.doesNotMatch(html, /featured-giant-wheel.*stage/i, '巨轮空降 must not be in the desktop feature stage');
assert.match(html, /const FEATURED_WORK_LIMIT = 5/, 'desktop feature stage must derive a fixed number of newest visible works');
assert.equal(new Set(works.map((work) => work.id)).size, works.length, 'catalog work ids must be unique');
assert.ok(works.every((work) => work.cnTitle && work.enTitle && work.cnSub && work.enSub && work.cnDesc && work.enDesc), 'catalog works must include titles, categories, and descriptions');
assert.ok(works.every((work) => !/新加入|可在管理页|newly added|admin page/i.test(`${work.cnDesc} ${work.enDesc}`)), 'public catalog metadata must not contain editor instructions');
assert.equal(works.find((work) => work.id === 'added-creative-3')?.cnTitle, '动作预演');
assert.equal(works.find((work) => work.id === 'added-v30001-0180')?.cnTitle, '街巷角色动画');
for (const work of works) {
  assert.ok(fs.existsSync(path.join(root, work.video)), `missing video for ${work.cnTitle}: ${work.video}`);
  for (const key of ['previewVideo', 'mobileVideo', 'webVideo']) if (work[key]) {
    assert.ok(fs.existsSync(path.join(root, work[key])), `missing ${key} for ${work.cnTitle}: ${work[key]}`);
  }
}
const snapshot = vm.runInNewContext(html.match(/const baseWorkData = (\[[\s\S]*?\n      \]);/)[1]);
assert.equal(JSON.stringify(snapshot), JSON.stringify(works), 'static fallback snapshot must retain all current media and metadata');
assert.equal((html.match(/class="no-js-work"/g) || []).length, works.length - 1, 'visible works must remain accessible without JavaScript');
assert.doesNotMatch(html, /<h3>巨轮空降<\/h3>/, '巨轮空降 must not appear in the primary works content');
