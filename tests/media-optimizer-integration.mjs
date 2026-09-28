import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import crypto from 'node:crypto';
import { spawnSync } from 'node:child_process';

const root = path.resolve(import.meta.dirname, '..');
const ffmpeg = process.env.FFMPEG_PATH || path.join(os.homedir(), '.cache/portfolio-media-tools/node_modules/ffmpeg-static/ffmpeg');
const temporary = fs.mkdtempSync(path.join(os.tmpdir(), 'portfolio-optimizer-'));
const run = (args) => {
  const result = spawnSync(ffmpeg, args, { encoding: 'utf8', maxBuffer: 8 * 1024 * 1024 });
  assert.equal(result.status, 0, result.stderr);
};
const digest = (file) => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const info = (file) => spawnSync(ffmpeg, ['-hide_banner', '-i', file], { encoding: 'utf8' }).stderr;
const duration = (text) => {
  const [, h, m, s] = text.match(/Duration: (\d+):(\d+):([\d.]+)/);
  return Number(h) * 3600 + Number(m) * 60 + Number(s);
};
const faststart = (file) => {
  const data = fs.readFileSync(file);
  const boxes = [];
  for (let offset = 0; offset + 8 <= data.length;) {
    boxes.push(data.toString('ascii', offset + 4, offset + 8));
    const size = data.readUInt32BE(offset);
    if (!size) break;
    offset += size === 1 ? Number(data.readBigUInt64BE(offset + 8)) : size;
  }
  return boxes.indexOf('moov') >= 0 && boxes.indexOf('moov') < boxes.indexOf('mdat');
};

try {
  fs.mkdirSync(path.join(temporary, 'data'));
  fs.mkdirSync(path.join(temporary, 'assets/works'), { recursive: true });
  const landscape = path.join(temporary, 'assets/works/landscape.mp4');
  const portrait = path.join(temporary, 'assets/works/portrait.mp4');
  run(['-v', 'error', '-f', 'lavfi', '-i', 'color=c=red:s=1600x900:r=12', '-f', 'lavfi', '-i', 'sine=frequency=440', '-t', '21', '-c:v', 'libx264', '-preset', 'ultrafast', '-pix_fmt', 'yuv420p', '-c:a', 'aac', landscape]);
  run(['-v', 'error', '-f', 'lavfi', '-i', 'color=c=blue:s=360x640:r=12', '-t', '4', '-c:v', 'libx264', '-preset', 'ultrafast', '-pix_fmt', 'yuv420p', portrait]);
  const originals = new Map([[landscape, digest(landscape)], [portrait, digest(portrait)]]);
  const catalogue = [
    { id: 'landscape', video: 'assets/works/landscape.mp4' },
    { id: 'portrait', video: 'assets/works/portrait.mp4' },
    { id: 'missing', video: 'assets/works/missing.mp4', previewVideo: 'assets/optimized/existing-preview.mp4', mobileVideo: 'assets/optimized/existing-mobile.mp4' },
  ];
  fs.writeFileSync(path.join(temporary, 'data/works.json'), JSON.stringify(catalogue));
  const generate = () => spawnSync(process.execPath, [path.join(root, 'scripts/optimize-media.mjs'), '--root', temporary], { encoding: 'utf8', env: { ...process.env, FFMPEG_PATH: ffmpeg }, maxBuffer: 8 * 1024 * 1024 });
  const first = generate();
  const output = JSON.parse(fs.readFileSync(path.join(temporary, 'data/works.json')));
  assert.ok(output[0].previewVideo, `valid works should generate despite another failure: ${first.stderr}`);
  assert.equal(first.status, 1, 'partial failure must be reported to the caller');
  const timestamps = new Map();
  for (const [index, expectedDuration, expectedMobileDimensions] of [[0, 20, '1280x720'], [1, 4, '360x640']]) {
    const work = output[index];
    for (const key of ['previewVideo', 'mobileVideo', 'webVideo']) {
      const file = path.join(temporary, work[key]);
      assert.match(work[key], new RegExp(`^assets/optimized/${work.id}/[a-f0-9]+-${key === 'previewVideo' ? 'preview' : key === 'mobileVideo' ? 'mobile' : 'web'}\\.mp4$`));
      assert.ok(faststart(file), `${key} must allow progressive playback`);
      run(['-v', 'error', '-i', file, '-f', 'null', '-']);
      timestamps.set(file, fs.statSync(file).mtimeMs);
    }
    const previewInfo = info(path.join(temporary, work.previewVideo));
    assert.ok(Math.abs(duration(previewInfo) - expectedDuration) < 0.15, 'preview must retain twenty seconds or full short original');
    assert.doesNotMatch(previewInfo, /Audio:/, 'previews must contain no audio stream');
    const dimensions = previewInfo.match(/Video:.*?, (\d+)x(\d+)(?=[ ,])/);
    assert.ok(Math.max(Number(dimensions[1]), Number(dimensions[2])) <= 960);
    assert.ok(fs.statSync(path.join(temporary, work.previewVideo)).size <= 2 * 1024 * 1024);
    assert.match(info(path.join(temporary, work.mobileVideo)), new RegExp(expectedMobileDimensions));
    assert.ok(Math.abs(duration(info(path.join(temporary, work.mobileVideo))) - duration(info(path.join(temporary, work.video)))) < 0.15);
  }
  assert.equal(output[2].previewVideo, catalogue[2].previewVideo, 'failed work retains prior media');
  assert.equal(output[2].mobileVideo, catalogue[2].mobileVideo);
  generate();
  for (const [file, mtime] of timestamps) assert.equal(fs.statSync(file).mtimeMs, mtime, 'repeat generation reuses verified hash-named resources');
  const modifiedTool = path.join(temporary, 'scripts');
  fs.mkdirSync(modifiedTool);
  fs.copyFileSync(path.join(root, 'scripts/sync-work-catalogue.mjs'), path.join(modifiedTool, 'sync-work-catalogue.mjs'));
  fs.writeFileSync(path.join(modifiedTool, 'optimize-media.mjs'), fs.readFileSync(path.join(root, 'scripts/optimize-media.mjs'), 'utf8').replaceAll("'-preset', 'veryfast'", "'-preset', 'superfast'"));
  spawnSync(process.execPath, [path.join(modifiedTool, 'optimize-media.mjs'), '--root', temporary], { encoding: 'utf8', env: { ...process.env, FFMPEG_PATH: ffmpeg } });
  const reconfigured = JSON.parse(fs.readFileSync(path.join(temporary, 'data/works.json')));
  assert.notEqual(reconfigured[0].previewVideo, output[0].previewVideo, 'changing encoding configuration must change its immutable resource URL');
  for (const [file, hash] of originals) assert.equal(digest(file), hash, 'original video must remain unchanged');
  console.log('media optimizer: profiles, twenty-second clips, no-upscale, decode, failure isolation, cache and originals PASS');
} finally {
  fs.rmSync(temporary, { recursive: true, force: true });
}
