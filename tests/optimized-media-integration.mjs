import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import crypto from 'node:crypto';
import { spawnSync } from 'node:child_process';

const root = path.resolve(import.meta.dirname, '..');
const ffmpeg = process.env.FFMPEG_PATH || path.join(os.homedir(), '.cache/portfolio-media-tools/node_modules/ffmpeg-static/ffmpeg');
const works = JSON.parse(fs.readFileSync(path.join(root, 'data/works.json')));
const report = JSON.parse(fs.readFileSync(path.join(root, 'assets/optimized/media-report.json')));
const run = args => {
  const result = spawnSync(ffmpeg, ['-hide_banner', '-nostdin', ...args], { encoding: 'utf8', maxBuffer: 8 * 1024 * 1024 });
  assert.equal(result.status, 0, result.stderr);
  return result.stdout;
};
const probe = file => {
  const text = spawnSync(ffmpeg, ['-hide_banner', '-i', file], { encoding: 'utf8' }).stderr;
  const video = text.split('\n').find(line => line.includes('Video:'));
  const [, h, m, s] = text.match(/Duration: (\d+):(\d+):([\d.]+)/);
  const [, width, height] = video.match(/, (\d+)x(\d+)(?=[ ,])/);
  return { text, video, seconds: +h * 3600 + +m * 60 + +s, width: +width, height: +height };
};
const isFaststart = file => {
  const fd = fs.openSync(file, 'r'), buffer = Buffer.alloc(16), boxes = [];
  try {
    for (let offset = 0; offset + 8 <= fs.fstatSync(fd).size;) {
      fs.readSync(fd, buffer, 0, 16, offset);
      boxes.push(buffer.toString('ascii', 4, 8));
      const size = buffer.readUInt32BE(0);
      if (!size) break;
      offset += size === 1 ? Number(buffer.readBigUInt64BE(8)) : size;
    }
  } finally { fs.closeSync(fd); }
  return boxes.indexOf('moov') >= 0 && boxes.indexOf('moov') < boxes.indexOf('mdat');
};
const digest = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
let previews = 0, mobiles = 0, originals = 0;
assert.equal(report.failed.length, 0);
assert.equal(report.previews.length, works.length);
for (const work of works) {
  const sourcePath = path.join(root, work.video), source = probe(sourcePath);
  assert.equal(digest(sourcePath), report.previews.find(row => row.id === work.id).sourceHash, 'original hash changed');
  if (process.env.SOURCE_BASELINE_ROOT) assert.equal(digest(sourcePath), digest(path.join(process.env.SOURCE_BASELINE_ROOT, work.video)), 'original differs from pre-optimization checkout');
  originals += fs.statSync(sourcePath).size;
  for (const key of ['previewVideo', 'mobileVideo']) {
    assert.ok(work[key], `${work.cnTitle} needs ${key}`);
    const file = path.join(root, work[key]), metadata = probe(file);
    assert.match(metadata.video, /Video: h264/);
    assert.match(metadata.video, /yuv420p/);
    assert.ok(isFaststart(file), `${work.cnTitle} ${key} not progressive`);
    run(['-v', 'error', '-i', file, '-f', 'null', '-']);
    if (key === 'previewVideo') {
      assert.doesNotMatch(metadata.text, /Audio:/);
      assert.ok(Math.abs(metadata.seconds - Math.min(20, source.seconds)) < 0.15);
      assert.ok(Math.max(metadata.width, metadata.height) <= 960);
      assert.ok(Number(metadata.video.match(/([\d.]+) fps/)?.[1]) <= 30);
      assert.ok(fs.statSync(file).size <= 2 * 1024 * 1024);
      previews += fs.statSync(file).size;
    } else {
      assert.ok(Math.max(metadata.width, metadata.height) <= 1280 && Math.min(metadata.width, metadata.height) <= 720);
      assert.ok(metadata.width <= source.width && metadata.height <= source.height);
      assert.ok(Math.abs(metadata.seconds - source.seconds) < 0.15);
      if (/Audio:/.test(source.text)) assert.match(metadata.text, /Audio: aac/);
      mobiles += fs.statSync(file).size;
    }
  }
  const desktop = path.join(root, work.webVideo || work.video);
  assert.ok(isFaststart(desktop), 'desktop full video needs front-loaded index');
  if (work.webVideo) assert.equal(run(['-v', 'error', '-i', desktop, '-map', '0:v:0', '-map', '0:a:0?', '-c', 'copy', '-f', 'hash', '-']), run(['-v', 'error', '-i', sourcePath, '-map', '0:v:0', '-map', '0:a:0?', '-c', 'copy', '-f', 'hash', '-']), 'remux must preserve full media packets');
}
const mib = bytes => (bytes / 1024 / 1024).toFixed(2);
const firstEight = works.slice(0, 8).reduce((sum, work) => sum + fs.statSync(path.join(root, work.previewVideo)).size, 0);
console.log(`${works.length} works PASS; originals ${mib(originals)} MiB, previews ${mib(previews)} MiB (first 8: ${mib(firstEight)} MiB), mobile ${mib(mobiles)} MiB. Decode, full durations, faststart and source integrity verified.`);
