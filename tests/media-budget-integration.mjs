import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { test } from 'node:test';

const root = path.resolve(import.meta.dirname, '..');
const works = JSON.parse(fs.readFileSync(path.join(root, 'data/works.json')));

test('legacy Hero clip and the five actual Hero previews stay below 3 MB', () => {
  const selected = ['work-reset-day-20261007', 'featured-prove-it', 'work-1783863606674-7ta9sp', 'featured-exported-film', 'featured-timeline-1'];
  const videos = ['assets/hero-fireflies.mp4', ...selected.map(id => works.find(work => work.id === id).previewVideo)];
  for (const name of videos) assert.ok(fs.statSync(path.join(root, name)).size < 3_000_000, `${name} exceeds 3 MB`);
});

test('every catalogue cover variant is a real WebP below 200 KB', () => {
  const manifest = JSON.parse(fs.readFileSync(path.join(root, 'data/image-variants.json')));
  for (const work of works) {
    assert.ok(manifest[work.poster]?.length, work.poster);
    for (const { src } of manifest[work.poster]) {
      const bytes = fs.readFileSync(path.join(root, src));
      assert.ok(src.endsWith('.webp'), src);
      assert.equal(bytes.toString('ascii', 8, 12), 'WEBP');
      assert.ok(bytes.length < 200_000, `${src}: ${bytes.length} bytes`);
    }
  }
});

test('project and reel cover images use budgeted WebP and lazy offscreen covers', () => {
  for (const page of ['projects.html', 'reel/index.html']) {
    const html = fs.readFileSync(path.join(root, page), 'utf8');
    const images = [...html.matchAll(/<img\b[^>]*\bsrc="([^"]+)"[^>]*>/g)];
    assert.ok(images.length >= 3);
    for (const [index, [tag, src]] of images.entries()) {
      assert.ok(src.endsWith('.webp'), `${page}: ${src}`);
      assert.ok(fs.statSync(path.resolve(root, path.dirname(page), src)).size < 200_000, src);
      if (index > 0) assert.match(tag, /\bloading="lazy"/, `${page}: ${src} must be lazy`);
    }
  }
});
