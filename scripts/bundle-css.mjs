// 把 index.html 引用的多个 CSS 按 head 里的顺序合并成一个 bundle，
// 减少首屏样式请求数（原来 14 个 <link>）。
//
//   源文件照旧在 assets/ 下按模块维护；改完样式后跑一次本脚本，
//   index.html 只引 assets/home-bundle.css。
//
//   用法：node scripts/bundle-css.mjs
import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(import.meta.dirname, '..');
const indexPath = path.join(root, 'index.html');
const html = fs.readFileSync(indexPath, 'utf8');

// 按 index.html 中出现的顺序抓 assets 下的 .css（忽略 ?v= 查询串），去重保序
const links = [...html.matchAll(/href="(assets\/[^"?]+\.css)(?:\?[^"]*)?"/g)].map((m) => m[1]);
const files = [...new Set(links)].filter((rel) => !rel.includes('home-bundle.css'));

if (files.length === 0) {
  console.error('✗ 没有在 index.html 里找到 assets/*.css 引用');
  process.exit(1);
}

const banner =
  '/* 自动生成 · 请勿手改。\n' +
  ' * 由 scripts/bundle-css.mjs 按 index.html 的 <link> 顺序合并以下源文件：\n' +
  files.map((f) => ' *   ' + f).join('\n') +
  '\n */\n';

const parts = [banner];
let total = 0;
for (const rel of files) {
  const p = path.join(root, rel);
  const css = fs.readFileSync(p, 'utf8');
  total += css.length;
  parts.push(`\n/* ==== ${rel} ==== */\n${css}`);
}

const out = path.join(root, 'assets/home-bundle.css');
fs.writeFileSync(out, parts.join(''));
const kb = (n) => (n / 1024).toFixed(1) + ' KB';
console.log(`已生成 assets/home-bundle.css：合并 ${files.length} 个源文件，源 ${kb(total)} → 产物 ${kb(fs.statSync(out).size)}`);
