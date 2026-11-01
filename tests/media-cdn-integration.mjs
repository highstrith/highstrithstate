import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { test } from 'node:test';

async function fixture(run) {
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'portfolio-cdn-'));
  const site = path.join(temp, 'site');
  const files = {
    'index.html': '<html><head><link rel="canonical" href="https://highstrith.github.io/highstrithstate/"><link href="assets/site.css"></head><body><img src="assets/cover.webp" srcset="assets/cover.webp 480w, assets/poster.jpg 960w"><a href="resume.html">Resume</a><a href="assets/cv.pdf">PDF</a><script src="assets/main.js"></script><script>const posterImageData={"assets/poster.jpg":[{"src":"assets/cover.webp"}]};</script><video data-src="assets/clip.mp4"></video></body></html>',
    'reel/index.html': '<html><head></head><body><img src="img/film.webp"><a href="../index.html">Home</a></body></html>',
    'assets/main.js': 'const poster="assets/cover.webp";const other="https://elsewhere.invalid/assets/cover.webp";',
    'assets/site.css': '.image{background:url("cover.webp")}',
    'data/works.json': JSON.stringify([{poster:'assets/poster.jpg',previewVideo:'assets/clip.mp4'}]),
    'assets/cover.webp': 'webp bytes', 'assets/poster.jpg': 'poster bytes',
    'assets/clip.mp4': 'video bytes', 'reel/img/film.webp': 'film bytes',
    'assets/cv.pdf': 'pdf bytes', 'assets/works/master.mp4': 'master bytes',
    'reel/img/raw/original.png': 'original bytes', 'assets/._private.png': 'metadata',
  };
  for (const [name, body] of Object.entries(files)) {
    fs.mkdirSync(path.dirname(path.join(site, name)), {recursive:true});
    fs.writeFileSync(path.join(site, name), body);
  }
  try {
    const { prepareMediaCdn } = await import('../scripts/prepare-media-cdn.mjs');
    await run({prepareMediaCdn,site,temp,files});
  } finally { fs.rmSync(temp, {recursive:true,force:true}); }
}

test('CDN publishing rewrites real media across static/dynamic views while keeping code, PDF and navigation on Pages', async () => {
  await fixture(({prepareMediaCdn,site,temp,files}) => {
    const mediaDir=path.join(temp,'upload');
    const report=prepareMediaCdn({siteDir:site,mediaDir,baseUrl:'https://cdn.example.test/portfolio/'});
    const html=fs.readFileSync(path.join(site,'index.html'),'utf8');
    assert.ok(html.includes('src="https://cdn.example.test/portfolio/assets/cover.webp"'));
    assert.ok(html.includes('https://cdn.example.test/portfolio/assets/poster.jpg 960w'));
    assert.ok(html.includes('"https://cdn.example.test/portfolio/assets/poster.jpg":'));
    assert.ok(html.includes('href="resume.html"'));
    assert.ok(html.includes('href="assets/cv.pdf"'));
    assert.ok(html.includes('src="assets/main.js"'));
    assert.ok(html.includes('href="assets/site.css"'));
    assert.ok(html.includes('window.STUDIO_MEDIA_BASE_URL="https://cdn.example.test/portfolio/"'));
    const script=fs.readFileSync(path.join(site,'assets/main.js'),'utf8');
    assert.ok(script.includes('poster="https://cdn.example.test/portfolio/assets/cover.webp"'));
    assert.ok(script.includes('https://elsewhere.invalid/assets/cover.webp'));
    assert.ok(fs.readFileSync(path.join(site,'assets/site.css'),'utf8').includes('url("https://cdn.example.test/portfolio/assets/cover.webp")'));
    assert.ok(fs.readFileSync(path.join(site,'reel/index.html'),'utf8').includes('https://cdn.example.test/portfolio/reel/img/film.webp'));
    assert.equal(JSON.parse(fs.readFileSync(path.join(site,'data/works.json')))[0].previewVideo,'https://cdn.example.test/portfolio/assets/clip.mp4');
    assert.deepEqual(report.files.map(f=>f.path).sort(),['assets/clip.mp4','assets/cover.webp','assets/poster.jpg','reel/img/film.webp']);
    for (const f of report.files) assert.equal(fs.readFileSync(path.join(mediaDir,f.path),'utf8'),files[f.path]);
    for (const forbidden of ['assets/main.js','assets/cv.pdf','assets/works/master.mp4','reel/img/raw/original.png','assets/._private.png']) assert.equal(fs.existsSync(path.join(mediaDir,forbidden)),false);
    prepareMediaCdn({siteDir:site,mediaDir,baseUrl:'https://cdn.example.test/portfolio/'});
    assert.equal(fs.readFileSync(path.join(site,'index.html'),'utf8'),html,'same CDN transform is idempotent');
  });
});

test('no CDN configuration leaves local and Pages references byte-for-byte unchanged', async () => {
  await fixture(({prepareMediaCdn,site,files}) => {
    prepareMediaCdn({siteDir:site,baseUrl:''});
    for (const [name,body] of Object.entries(files)) assert.equal(fs.readFileSync(path.join(site,name),'utf8'),body);
  });
});

test('unsafe CDN URLs and overlapping output directories are rejected before changing files', async () => {
  await fixture(({prepareMediaCdn,site,files}) => {
    for (const baseUrl of ['http://cdn.example.test/','https://user:secret@cdn.example.test/','https://cdn.example.test/?token=secret','javascript:alert(1)']) {
      assert.throws(()=>prepareMediaCdn({siteDir:site,baseUrl}));
    }
    assert.throws(()=>prepareMediaCdn({siteDir:site,mediaDir:site,baseUrl:'https://cdn.example.test/'}));
    assert.equal(fs.readFileSync(path.join(site,'index.html'),'utf8'),files['index.html']);
  });
});
