// Publish-time transformation only. Source media paths remain portable/local.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { pathToFileURL } from 'node:url';

const mediaExtension = /\.(?:webp|avif|png|jpe?g|gif|svg|mp4|webm)$/i;
const textExtension = /\.(?:html|js|json|css)$/i;
const blocked = /(?:^|\/)(?:\.[^/]*|originals|raw)(?:\/|$)|^assets\/works\//;
const inside = (parent, child) => child === parent || child.startsWith(parent + path.sep);

export function prepareMediaCdn({siteDir, mediaDir, baseUrl = ''}) {
  siteDir = fs.realpathSync(path.resolve(siteDir));
  let base;
  if (baseUrl) {
    base = new URL(baseUrl);
    const local = ['localhost', '127.0.0.1', '[::1]'].includes(base.hostname);
    if ((base.protocol !== 'https:' && !(local && base.protocol === 'http:')) || base.username || base.password || base.search || base.hash) {
      throw new Error('Use a public HTTPS CDN base without credentials, query or fragment.');
    }
    if (!base.pathname.endsWith('/')) base.pathname += '/';
  }
  if (mediaDir) {
    mediaDir = path.resolve(mediaDir);
    let ancestor = mediaDir;
    while (!fs.existsSync(ancestor)) ancestor = path.dirname(ancestor);
    mediaDir = path.join(fs.realpathSync(ancestor), path.relative(ancestor, mediaDir));
    if (inside(siteDir, mediaDir) || inside(mediaDir, siteDir)) throw new Error('Media output must be separate from the published site.');
  }
  const files = [];
  const walk = directory => {
    for (const entry of fs.readdirSync(directory, {withFileTypes:true})) {
      const absolute = path.join(directory, entry.name);
      const relative = path.relative(siteDir, absolute).split(path.sep).join('/');
      if (blocked.test(relative)) continue;
      if (entry.isDirectory()) walk(absolute);
      else if (entry.isFile()) files.push(relative);
    }
  };
  walk(siteDir);
  const media = files.filter(name => /^(?:assets\/|reel\/img\/)/.test(name) && mediaExtension.test(name));
  const whitelist = new Set(media);
  const report = {baseUrl:base?.href || '',files:media.map(name => {
    const file = path.join(siteDir, name);
    return {path:name,bytes:fs.statSync(file).size,sha256:crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex')};
  })};
  if (mediaDir) {
    for (const name of media) {
      const destination = path.join(mediaDir, name);
      fs.mkdirSync(path.dirname(destination), {recursive:true});
      fs.copyFileSync(path.join(siteDir, name), destination);
    }
  }
  if (!base) return report;
  const origin = 'https://media-build.invalid/';
  const index = fs.existsSync(path.join(siteDir, 'index.html')) ? fs.readFileSync(path.join(siteDir, 'index.html'), 'utf8') : '';
  const canonical = index.match(/<link\b[^>]*rel=["']canonical["'][^>]*href=["']([^"']+)/i)?.[1];
  const reference = /(?:https?:\/\/)?[a-zA-Z0-9_.%+~/-]+\.(?:webp|avif|png|jpe?g|gif|svg|mp4|webm)(?:\?[^\s"'<>)]*)?/gi;
  for (const name of files.filter(name => textExtension.test(name))) {
    const file = path.join(siteDir, name);
    const original = fs.readFileSync(file, 'utf8');
    let result = original.replace(reference, value => {
      const rootRelative = /^(?:assets\/|reel\/)/.test(value);
      const resolutionBase = rootRelative ? origin : new URL(name, origin);
      const url = new URL(value, resolutionBase);
      let key;
      if (url.origin === new URL(origin).origin) key = decodeURIComponent(url.pathname.slice(1));
      else if (canonical && url.href.startsWith(canonical)) key = decodeURIComponent(url.href.slice(canonical.length).split('?')[0]);
      if (!whitelist.has(key)) return value;
      return new URL(key, base).href + url.search + url.hash;
    });
    if (name.endsWith('.html')) {
      const config = `<script data-media-cdn>window.STUDIO_MEDIA_BASE_URL=${JSON.stringify(base.href).replace(/</g, '\\u003c')};</script>`;
      if (/<script data-media-cdn>[\s\S]*?<\/script>/.test(result)) result = result.replace(/<script data-media-cdn>[\s\S]*?<\/script>/, config);
      else result = result.replace(/<head\b[^>]*>/i, head => head + config);
    }
    if (result !== original) fs.writeFileSync(file, result);
  }
  return report;
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  const arg = name => {const i=process.argv.indexOf(name);return i<0?undefined:process.argv[i+1];};
  const report = prepareMediaCdn({siteDir:arg('--site') || 'public',mediaDir:arg('--media-dir'),baseUrl:arg('--base') || process.env.MEDIA_CDN_BASE_URL || ''});
  console.log(JSON.stringify({baseUrl:report.baseUrl,files:report.files.length,bytes:report.files.reduce((sum,file)=>sum+file.bytes,0)}));
}
