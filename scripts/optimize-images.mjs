// Local build tool only. Originals and works.json are never rewritten.
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import crypto from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';

const sha = (file) => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const writeJSON = (file, value) => {
  const content = JSON.stringify(value, null, 2) + '\n';
  if (fs.existsSync(file) && fs.readFileSync(file, 'utf8') === content) return;
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const temporary = `${file}.${process.pid}.tmp`;
  fs.writeFileSync(temporary, content);
  fs.renameSync(temporary, file);
};

export function optimizeImages(root) {
  root = fs.realpathSync(path.resolve(root));
  const ffmpeg = process.env.FFMPEG_PATH || path.join(os.homedir(), '.cache/portfolio-media-tools/node_modules/ffmpeg-static/ffmpeg');
  if (!fs.existsSync(ffmpeg)) throw new Error('Set FFMPEG_PATH or use the existing ~/.cache/portfolio-media-tools FFmpeg.');
  const run = (args, check = true) => {
    const result = spawnSync(ffmpeg, ['-hide_banner', '-nostdin', ...args], { encoding: 'utf8', maxBuffer: 8 * 1024 * 1024 });
    if (check && result.status !== 0) throw new Error(result.stderr || String(result.error));
    return result;
  };
  const inspect = (file) => {
    const stream = run(['-i', file], false).stderr.split('\n').find(line => /Video:/.test(line));
    const dimensions = stream?.match(/, (\d+)x(\d+)(?=[ ,])/);
    if (!dimensions) throw new Error(`No readable image: ${file}`);
    return { width: Number(dimensions[1]), height: Number(dimensions[2]) };
  };
  const profile = { widths: [160, 480, 960, 1600], quality: 80, codec: 'libwebp', preset: 'picture', compressionLevel: 6, scale: 'lanczos', version: 1 };
  const toolHash = sha(ffmpeg);
  const profileHash = crypto.createHash('sha256').update(JSON.stringify(profile) + toolHash).digest('hex').slice(0, 8);
  const worksFile = path.join(root, 'data/works.json');
  const worksHash = sha(worksFile);
  const works = JSON.parse(fs.readFileSync(worksFile));
  const sources = [...new Set([...works.map(work => work.poster).filter(Boolean), 'assets/hero-digital-human-full.jpg'])].sort();
  const directory = path.join(root, 'assets/optimized-images');
  fs.mkdirSync(directory, { recursive: true });
  const manifest = {};
  const report = { tool: run(['-version']).stdout.split('\n')[0], toolHash, profile, sources: [] };

  for (const sourcePath of sources) {
    if (typeof sourcePath !== 'string' || !sourcePath.startsWith('assets/') || sourcePath.includes('\\') || /(^|\/)\.\.?(\/|$)/.test(sourcePath)) throw new Error('Source must stay within assets.');
    const source = fs.realpathSync(path.resolve(root, sourcePath));
    const boundary = path.relative(fs.realpathSync(path.join(root, 'assets')), source);
    if (boundary.startsWith('..') || path.isAbsolute(boundary) || !fs.statSync(source).isFile()) throw new Error('Source must be a regular file inside assets.');
    const sourceHash = sha(source);
    const info = inspect(source);
    const variants = [];
    const metrics = [];
    const widths = [...new Set(profile.widths.map(width => Math.min(width, info.width)))];
    for (const width of widths) {
      const height = Math.max(1, Math.round(info.height * width / info.width));
      const output = path.join(directory, `${sourceHash.slice(0, 16)}-${profileHash}-${width}w.webp`);
      const validate = (file) => {
        const size = inspect(file);
        if (size.width !== width || size.height !== height) throw new Error('Cached image dimensions do not match its profile.');
        run(['-v', 'error', '-i', file, '-f', 'null', '-']);
      };
      let cached = false;
      if (fs.existsSync(output)) {
        try { validate(output); cached = true; } catch (_) { /* Regenerate an unreadable cache without changing source data. */ }
      }
      if (!cached) {
        const temporary = output.replace(/\.webp$/, `.${process.pid}.tmp.webp`);
        try {
          run(['-v', 'error', '-y', '-i', source, '-vf', `scale=${width}:${height}:flags=lanczos`, '-frames:v', '1', '-c:v', 'libwebp', '-preset', 'picture', '-quality', '80', '-compression_level', '6', '-map_metadata', '-1', temporary]);
          validate(temporary);
          fs.renameSync(temporary, output);
        } finally { if (fs.existsSync(temporary)) fs.unlinkSync(temporary); }
      }
      const src = path.relative(root, output).split(path.sep).join('/');
      variants.push({ src, width, height });
      metrics.push({ src, width, height, bytes: fs.statSync(output).size, sha256: sha(output) });
    }
    if (sha(source) !== sourceHash) throw new Error(`Source changed during build: ${sourcePath}`);
    manifest[sourcePath] = variants;
    report.sources.push({ source: sourcePath, sourceHash, ...info, bytes: fs.statSync(source).size, variants: metrics });
    console.log(`${sourcePath}: ${fs.statSync(source).size} B → ${metrics.map(v => `${v.width}w ${v.bytes} B`).join(', ')}`);
  }
  if (sha(worksFile) !== worksHash) throw new Error('works.json changed during image build.');
  writeJSON(path.join(root, 'data/image-variants.json'), manifest);
  writeJSON(path.join(directory, 'image-report.json'), report);
  console.log(`Finished: ${sources.length} preserved source images, ${Object.values(manifest).flat().length} WebP variants; quality ${profile.quality}.`);
  return manifest;
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  const rootArg = process.argv.indexOf('--root');
  optimizeImages(rootArg >= 0 ? process.argv[rootArg + 1] : path.resolve(import.meta.dirname, '..'));
}
