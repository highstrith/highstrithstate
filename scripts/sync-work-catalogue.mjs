import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const escapeHtml = value => String(value || '').replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
const CARD_SIZES = '(max-width: 600px) calc(100vw - 40px), (max-width: 1100px) calc((100vw - 96px) / 2), (max-width: 1696px) calc((100vw - 128px) / 2), 784px';
const HERO_SIZES = '(max-width: 600px) calc(100vw - 40px), (max-width: 1100px) calc(100vw - 64px), (max-width: 1696px) calc(100vw - 96px), 1600px';
const PORTRAIT_SIZES = '(max-width: 600px) calc(100vw - 40px), (max-width: 1100px) 40vw, (max-width: 1696px) 43vw, 684px';
const safeAsset = value => {
  if (typeof value !== 'string' || !value.startsWith('assets/') || value.includes('\\') || /(^|\/)\.\.?(\/|$)|[\u0000-\u001f]/.test(value)) return false;
  try { return new URL(value, 'https://portfolio.invalid/').href.startsWith('https://portfolio.invalid/assets/'); } catch (_) { return false; }
};

function readImageManifest(root) {
  const manifest = path.join(root, 'data/image-variants.json');
  if (!fs.existsSync(manifest)) return {};
  let payload;
  try { payload = JSON.parse(fs.readFileSync(manifest, 'utf8')); } catch (_) { return {}; }
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) return {};
  const result = {};
  for (const [source, variants] of Object.entries(payload)) {
    if (!safeAsset(source) || !Array.isArray(variants)) continue;
    const seen = new Set();
    const valid = variants.filter(variant => variant && safeAsset(variant.src) &&
      Number.isInteger(variant.width) && variant.width > 0 && Number.isInteger(variant.height) && variant.height > 0)
      .sort((a, b) => a.width - b.width)
      .filter(variant => { if (seen.has(variant.width)) return false; seen.add(variant.width); return true; })
      .map(({ src, width, height }) => ({ src, width, height }));
    if (valid.length) result[source] = valid;
  }
  return result;
}

function imageAttributes(source, images, sizes) {
  const variants = images[source];
  if (!variants?.length) return `src="${escapeHtml(source)}"`;
  const initial = variants.find(variant => variant.width >= 480) || variants.at(-1);
  const srcset = variants.map(variant => `${variant.src} ${variant.width}w`).join(', ');
  return `src="${escapeHtml(initial.src)}" srcset="${escapeHtml(srcset)}" sizes="${escapeHtml(sizes)}" width="${initial.width}" height="${initial.height}"`;
}

function syncStaticImages(html, images) {
  const attribute = (tag, name) => {
    const value = tag.match(new RegExp(`\\s${name}=(?:"([^"]*)"|'([^']*)')`, 'i'));
    return (value?.[1] ?? value?.[2] ?? '').replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');
  };
  return html.replace(/<img\b[^>]*>/gi, tag => {
    const hero = attribute(tag, 'id') === 'heroPoster';
    const portrait = attribute(tag, 'class').split(/\s+/).includes('hero-avatar');
    if (!hero && !portrait) return tag;
    const source = attribute(tag, 'data-image-source') || attribute(tag, 'src');
    if (!source) return tag;
    const cleaned = tag.replace(/\s(?:src|srcset|sizes|width|height|data-image-source)=(?:"[^"]*"|'[^']*')/gi, '');
    return cleaned.replace(/\s*\/?\s*>$/, ` ${imageAttributes(source, images, hero ? HERO_SIZES : PORTRAIT_SIZES)} data-image-source="${escapeHtml(source)}">`);
  });
}

export function syncWorkCatalogue(root) {
  const file = path.join(root, 'index.html');
  if (!fs.existsSync(file)) return;
  const works = JSON.parse(fs.readFileSync(path.join(root, 'data/works.json')));
  const visibleWorks = works.filter(work => work.id !== 'featured-giant-wheel')
    .sort((a, b) => (Date.parse(b.createdAt) || 0) - (Date.parse(a.createdAt) || 0));
  const images = readImageManifest(root);
  const snapshot = JSON.stringify(works, null, 2).replace(/</g, '\\u003c').replace(/\n/g, '\n      ');
  const fallback = '<div class="works-grid">\n' + visibleWorks.map(work => `<a class="no-js-work" href="${escapeHtml(work.webVideo || work.video)}">${work.poster ? `<img ${imageAttributes(work.poster, images, CARD_SIZES)} alt="" loading="lazy" />` : ''}<h3>${escapeHtml(work.cnTitle)}</h3><p>${escapeHtml(work.cnSub)} · 播放完整作品</p></a>`).join('\n') + '\n</div>';
  const before = fs.readFileSync(file, 'utf8');
  if (!/const baseWorkData = \[[\s\S]*?\n      \];/.test(before) || !/<!-- generated-works:start -->[\s\S]*?<!-- generated-works:end -->/.test(before)) throw new Error('Catalogue markers missing from index.html.');
  let after = before.replace(/const baseWorkData = \[[\s\S]*?\n      \];/, () => `const baseWorkData = ${snapshot};`).replace(/<!-- generated-works:start -->[\s\S]*?<!-- generated-works:end -->/, () => `<!-- generated-works:start -->\n${fallback}\n          <!-- generated-works:end -->`);
  const imageSnapshot = JSON.stringify(images, null, 2).replace(/</g, '\\u003c');
  after = after.replace(/<!-- generated-images:start -->[\s\S]*?<!-- generated-images:end -->/, () => `<!-- generated-images:start -->\n  <script>const posterImageData = ${imageSnapshot};</script>\n  <!-- generated-images:end -->`);
  after = syncStaticImages(after, images);
  if (after !== before) fs.writeFileSync(file, after);
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  syncWorkCatalogue(path.resolve(import.meta.dirname, '..'));
  console.log('Static snapshot and no-JavaScript work links synchronized.');
}
