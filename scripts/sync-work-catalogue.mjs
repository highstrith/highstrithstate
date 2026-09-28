import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const escapeHtml = value => String(value || '').replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));

export function syncWorkCatalogue(root) {
  const file = path.join(root, 'index.html');
  if (!fs.existsSync(file)) return;
  const works = JSON.parse(fs.readFileSync(path.join(root, 'data/works.json')));
  const snapshot = JSON.stringify(works, null, 2).replace(/</g, '\\u003c').replace(/\n/g, '\n      ');
  const fallback = '<div class="works-grid">\n' + works.map(work => `<a class="no-js-work" href="${escapeHtml(work.webVideo || work.video)}">${work.poster ? `<img src="${escapeHtml(work.poster)}" alt="" loading="lazy" />` : ''}<h3>${escapeHtml(work.cnTitle)}</h3><p>${escapeHtml(work.cnSub)} · 播放完整作品</p></a>`).join('\n') + '\n</div>';
  const before = fs.readFileSync(file, 'utf8');
  if (!/const baseWorkData = \[[\s\S]*?\n      \];/.test(before) || !/<!-- generated-works:start -->[\s\S]*?<!-- generated-works:end -->/.test(before)) throw new Error('Catalogue markers missing from index.html.');
  const after = before.replace(/const baseWorkData = \[[\s\S]*?\n      \];/, () => `const baseWorkData = ${snapshot};`).replace(/<!-- generated-works:start -->[\s\S]*?<!-- generated-works:end -->/, () => `<!-- generated-works:start -->\n${fallback}\n          <!-- generated-works:end -->`);
  if (after !== before) fs.writeFileSync(file, after);
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  syncWorkCatalogue(path.resolve(import.meta.dirname, '..'));
  console.log('Static snapshot and no-JavaScript work links synchronized.');
}
