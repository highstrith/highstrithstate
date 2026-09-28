import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import vm from 'node:vm';
import { test } from 'node:test';
import { syncWorkCatalogue } from '../scripts/sync-work-catalogue.mjs';

const template = fs.readFileSync(path.join(import.meta.dirname, '../index.html'), 'utf8');
const fixtures = [
  ['$$', '$$'],
  ['$&', '$&amp;'],
  ['$`', '$`'],
  ["$'", '$&#39;'],
  ['</script><script>throw new Error("metadata")</script>', '&lt;/script&gt;&lt;script&gt;throw new Error(&quot;metadata&quot;)&lt;/script&gt;'],
];

for (const [metadata, escaped] of fixtures) {
  test(`catalogue sync preserves literal ${metadata} and safe HTML`, () => {
    const temporary = fs.mkdtempSync(path.join(os.tmpdir(), 'portfolio-catalogue-'));
    try {
      fs.mkdirSync(path.join(temporary, 'data'));
      fs.writeFileSync(path.join(temporary, 'index.html'), template);
      const works = [{
        id: 'literal-metadata',
        cnTitle: `Title ${metadata}`,
        enTitle: `English ${metadata}`,
        cnSub: `Description ${metadata}`,
        enSub: `English description ${metadata}`,
        cnDesc: `Details ${metadata}`,
        enDesc: `English details ${metadata}`,
        video: 'assets/works/original.mp4',
        webVideo: `assets/optimized/full-${metadata}.mp4?x="&y=1`,
        poster: `assets/posters/cover-${metadata}.jpg?x="&y=1`,
      }];
      fs.writeFileSync(path.join(temporary, 'data/works.json'), JSON.stringify(works));

      syncWorkCatalogue(temporary);
      const html = fs.readFileSync(path.join(temporary, 'index.html'), 'utf8');
      const inlineScripts = [...html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script\s*>/gi)];
      assert.equal(inlineScripts.length, [...template.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script\s*>/gi)].length, 'metadata must not add script elements');
      for (const [, script] of inlineScripts) assert.doesNotThrow(() => new vm.Script(script), 'all inline scripts must compile');
      const declaration = html.match(/const baseWorkData = \[[\s\S]*?\n      \];/)?.[0];
      assert.ok(declaration, 'the static catalogue must remain readable');
      assert.deepEqual(JSON.parse(vm.runInNewContext(`${declaration}\nJSON.stringify(baseWorkData);`)), works, 'static metadata must round-trip without replacement expansion');

      const fallback = html.match(/<noscript>([\s\S]*?)<\/noscript>/)?.[1];
      assert.ok(fallback, 'no-JavaScript catalogue must remain available');
      assert.ok(fallback.includes(`<h3>Title ${escaped}</h3>`), 'fallback title must preserve literal text safely');
      assert.ok(fallback.includes(`<p>Description ${escaped} · 播放完整作品</p>`), 'fallback description must preserve literal text safely');
      assert.ok(fallback.includes(`href="assets/optimized/full-${escaped}.mp4?x=&quot;&amp;y=1"`), 'complete playback link must survive replacement and HTML escaping');
      assert.ok(fallback.includes(`src="assets/posters/cover-${escaped}.jpg?x=&quot;&amp;y=1"`), 'poster link must survive replacement and HTML escaping');
      assert.doesNotMatch(fallback, /<\/?script\b/i, 'fallback metadata must not become markup');
    } finally {
      fs.rmSync(temporary, { recursive: true, force: true });
    }
  });
}
