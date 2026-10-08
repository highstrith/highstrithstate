import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import crypto from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { test } from 'node:test';

const project = path.resolve(import.meta.dirname, '..');
const script = path.join(project, 'scripts/optimize-images.mjs');
const hash = (file) => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const ffmpeg = process.env.FFMPEG_PATH || path.join(os.homedir(), '.cache/portfolio-media-tools/node_modules/ffmpeg-static/ffmpeg');
const imageSize = (file) => {
  const result = spawnSync(ffmpeg, ['-hide_banner', '-i', file], { encoding: 'utf8' });
  const dimensions = result.stderr.match(/Video:.*?, (\d+)x(\d+)(?=[ ,])/);
  assert.ok(dimensions, result.stderr);
  return dimensions.slice(1).map(Number);
};

test('image build preserves source bytes, caps widths and reproduces valid content-hashed WebP', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'portfolio-image-build-'));
  try {
    fs.mkdirSync(path.join(root, 'assets/posters'), { recursive: true });
    fs.mkdirSync(path.join(root, 'data'));
    for (const [from, to] of [
      ['assets/uploads/posters/reset-day-20261007-16x9.png', 'assets/posters/large.png'],
      ['assets/uploads/posters/poster-1783864071336.png', 'assets/posters/small.png'],
      ['assets/hero-digital-human-full.jpg', 'assets/hero-digital-human-full.jpg'],
    ]) fs.copyFileSync(path.join(project, from), path.join(root, to));
    const works = [{ id: 'large', poster: 'assets/posters/large.png' }, { id: 'small', poster: 'assets/posters/small.png' }];
    fs.writeFileSync(path.join(root, 'data/works.json'), JSON.stringify(works));
    fs.writeFileSync(path.join(root, 'index.html'), 'Untouched source page');
    const originals = [...works.map(w => w.poster), 'assets/hero-digital-human-full.jpg', 'data/works.json', 'index.html'];
    const before = Object.fromEntries(originals.map(p => [p, hash(path.join(root, p))]));
    const build = () => {
      const result = spawnSync(process.execPath, [script, '--root', root], { encoding: 'utf8' });
      assert.equal(result.status, 0, result.stderr);
      return JSON.parse(fs.readFileSync(path.join(root, 'data/image-variants.json')));
    };
    const manifest = build();
    assert.deepEqual(Object.keys(manifest).sort(), ['assets/hero-digital-human-full.jpg', 'assets/posters/large.png', 'assets/posters/small.png']);
    assert.deepEqual(manifest['assets/posters/large.png'].map(v => v.width), [160, 480, 960, 1600]);
    assert.deepEqual(manifest['assets/posters/small.png'].map(v => v.width), [160, 480, 568]);
    for (const [source, variants] of Object.entries(manifest)) {
      const [width, height] = imageSize(path.join(root, source));
      for (const variant of variants) {
        assert.ok(variant.src.startsWith('assets/optimized-images/'));
        assert.ok(variant.src.includes(before[source].slice(0, 16)), 'replacement source bytes must invalidate URL');
        assert.ok(variant.width <= width && variant.height <= height, 'no upscaling');
        assert.ok(Math.abs(variant.height - height * variant.width / width) <= 1, 'full aspect ratio must survive resizing');
        assert.deepEqual(imageSize(path.join(root, variant.src)), [variant.width, variant.height]);
        const decode = spawnSync(ffmpeg, ['-v', 'error', '-i', path.join(root, variant.src), '-f', 'null', '-'], { encoding: 'utf8' });
        assert.equal(decode.status, 0, decode.stderr);
      }
    }
    for (const p of originals) assert.equal(hash(path.join(root, p)), before[p], `${p} must remain byte-for-byte unchanged`);
    const outputHashes = Object.fromEntries(Object.values(manifest).flat().map(v => [v.src, hash(path.join(root, v.src))]));
    assert.deepEqual(build(), manifest, 'rerun must keep manifest stable');
    const regenerated = manifest['assets/posters/large.png'][0].src;
    fs.unlinkSync(path.join(root, regenerated));
    assert.deepEqual(build(), manifest);
    for (const [p, digest] of Object.entries(outputHashes)) assert.equal(hash(path.join(root, p)), digest, 'regenerated and cached output must reproduce the same bytes');
    fs.copyFileSync(path.join(project, 'assets/uploads/posters/lying-down-20261001-16x9.png'), path.join(root, 'assets/posters/large.png'));
    assert.notEqual(build()['assets/posters/large.png'][0].src, manifest['assets/posters/large.png'][0].src, 'changed source must get a new asset URL');
  } finally { fs.rmSync(root, { recursive: true, force: true }); }
});
