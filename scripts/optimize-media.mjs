// Local-only build tool. No FFmpeg binary or npm dependency is shipped to Pages.
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import crypto from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { syncWorkCatalogue } from './sync-work-catalogue.mjs';

const rootArg = process.argv.indexOf('--root');
const root = fs.realpathSync(path.resolve(rootArg >= 0 ? process.argv[rootArg + 1] : path.join(import.meta.dirname, '..')));
const ffmpeg = process.env.FFMPEG_PATH || path.join(os.homedir(), '.cache/portfolio-media-tools/node_modules/ffmpeg-static/ffmpeg');
if (!fs.existsSync(ffmpeg)) throw new Error('Install ffmpeg-static@5.3.0 in ~/.cache/portfolio-media-tools, or set FFMPEG_PATH.');
const run = (args, check = true) => {
  const result = spawnSync(ffmpeg, ['-hide_banner', '-nostdin', ...args], { encoding: 'utf8', maxBuffer: 8 * 1024 * 1024 });
  if (check && result.status !== 0) throw new Error(result.stderr || String(result.error));
  return result;
};
const sha = (file) => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const toolHash = sha(ffmpeg);
const inspect = (file) => {
  const text = run(['-i', file], false).stderr;
  const clock = text.match(/Duration: (\d+):(\d+):([\d.]+)/);
  const stream = text.split('\n').find(line => /Video:/.test(line));
  const size = stream?.match(/, (\d+)x(\d+)(?=[ ,])/);
  if (!clock || !size) throw new Error(`No readable video: ${file}`);
  const rotation = Number(text.match(/rotation of ([\d.-]+)/)?.[1] || 0);
  const rotated = Math.abs(Math.round(rotation / 90)) % 2 === 1;
  return {
    duration: Number(clock[1]) * 3600 + Number(clock[2]) * 60 + Number(clock[3]),
    width: Number(size[rotated ? 2 : 1]), height: Number(size[rotated ? 1 : 2]),
    fps: Math.min(30, Number(stream.match(/([\d.]+) fps/)?.[1] || 30)),
  };
};
const faststart = (file) => {
  const fd = fs.openSync(file, 'r');
  const header = Buffer.alloc(16);
  let moov = -1, mdat = -1;
  try {
    for (let offset = 0; offset + 8 <= fs.fstatSync(fd).size;) {
      fs.readSync(fd, header, 0, 16, offset);
      const name = header.toString('ascii', 4, 8);
      if (name === 'moov') moov = offset;
      if (name === 'mdat') mdat = offset;
      const shortSize = header.readUInt32BE(0);
      const size = shortSize === 1 ? Number(header.readBigUInt64BE(8)) : shortSize;
      if (size < 8) break;
      offset += size;
    }
  } finally { fs.closeSync(fd); }
  return moov >= 0 && mdat >= 0 && moov < mdat;
};
const scaled = (info, longEdge, shortEdge = longEdge) => {
  const ratio = Math.min(1, longEdge / Math.max(info.width, info.height), shortEdge / Math.min(info.width, info.height));
  return `${Math.max(2, Math.floor(info.width * ratio / 2) * 2)}:${Math.max(2, Math.floor(info.height * ratio / 2) * 2)}`;
};
const cataloguePath = path.join(root, 'data/works.json');
const works = JSON.parse(fs.readFileSync(cataloguePath));
const report = { tool: run(['-version']).stdout.split('\n')[0], toolHash, previews: [], failed: [] };
// Include the generator itself so changing any fixed encoding option invalidates
// cached files, even when it is not one of the main profile values below.
const profile = { version: 1, seconds: 20, previewEdge: 960, previewBitrate: '650k', mobileLongEdge: 1280, mobileShortEdge: 720, mobileCRF: 25, mobileMaxrate: '3M', fpsLimit: 30, toolHash, generatorHash: sha(import.meta.filename) };

for (const work of works) {
  try {
    const source = fs.realpathSync(path.resolve(root, work.video));
    const relative = path.relative(path.join(root, 'assets'), source);
    if (relative.startsWith('..') || path.isAbsolute(relative)) throw new Error('Source is outside assets.');
    const sourceHash = sha(source);
    const info = inspect(source);
    const hash = crypto.createHash('sha256').update(sourceHash + JSON.stringify(profile)).digest('hex').slice(0, 16);
    const directory = path.join(root, 'assets/optimized', String(work.id).replace(/[^a-zA-Z0-9_-]/g, '_'));
    fs.mkdirSync(directory, { recursive: true });
    const encode = (kind, args) => {
      const output = path.join(directory, `${hash}-${kind}.mp4`);
      if (!fs.existsSync(output)) {
        const temporary = path.join(directory, `${hash}-${kind}.tmp.mp4`);
        try {
          run(['-v', 'error', '-y', ...args, temporary]);
          run(['-v', 'error', '-i', temporary, '-f', 'null', '-']);
          if (!faststart(temporary)) throw new Error(`${kind} is not faststart.`);
          if (kind === 'preview' && fs.statSync(temporary).size > 2 * 1024 * 1024) throw new Error('Preview exceeds 2 MiB.');
          fs.renameSync(temporary, output);
        } finally { if (fs.existsSync(temporary)) fs.unlinkSync(temporary); }
      }
      return path.relative(root, output).split(path.sep).join('/');
    };
    const previewVideo = encode('preview', ['-ss', String(Math.min(info.duration * 0.2, Math.max(0, info.duration - 20))), '-i', source, '-t', '20', '-map', '0:v:0', '-an', '-vf', `scale=${scaled(info, 960)}`, '-r', String(info.fps), '-c:v', 'libx264', '-preset', 'veryfast', '-threads', '2', '-b:v', '650k', '-maxrate', '700k', '-bufsize', '1400k', '-pix_fmt', 'yuv420p', '-movflags', '+faststart']);
    const mobileVideo = encode('mobile', ['-i', source, '-map', '0:v:0', '-map', '0:a:0?', '-vf', `scale=${scaled(info, 1280, 720)}`, '-r', String(info.fps), '-c:v', 'libx264', '-preset', 'veryfast', '-threads', '2', '-crf', '25', '-maxrate', '3M', '-bufsize', '6M', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '96k', '-movflags', '+faststart']);
    const webVideo = faststart(source) ? '' : encode('web', ['-i', source, '-map', '0:v:0', '-map', '0:a:0?', '-c', 'copy', '-movflags', '+faststart']);
    if (sha(source) !== sourceHash) throw new Error('Source changed while generating.');
    Object.assign(work, { previewVideo, mobileVideo, webVideo });
    const previewInfo = inspect(path.join(root, previewVideo));
    report.previews.push({ id: work.id, source: work.video, sourceHash, previewSeconds: previewInfo.duration, previewBytes: fs.statSync(path.join(root, previewVideo)).size, mobileBytes: fs.statSync(path.join(root, mobileVideo)).size, webRemux: !!webVideo });
    console.log(`${work.cnTitle || work.id}: ${previewInfo.duration}s preview; mobile ready${webVideo ? '; desktop faststart' : ''}`);
  } catch (error) {
    report.failed.push({ id: work.id, error: error.message });
    console.error(`${work.cnTitle || work.id}: ${error.message}`);
  }
}
const temporaryCatalogue = cataloguePath + '.tmp';
fs.writeFileSync(temporaryCatalogue, JSON.stringify(works, null, 2) + '\n');
fs.renameSync(temporaryCatalogue, cataloguePath);
fs.mkdirSync(path.join(root, 'assets/optimized'), { recursive: true });
fs.writeFileSync(path.join(root, 'assets/optimized/media-report.json'), JSON.stringify(report, null, 2) + '\n');
syncWorkCatalogue(root);
console.log(`Finished: ${report.previews.length} optimized, ${report.failed.length} failed.`);
if (report.failed.length) process.exitCode = 1;
