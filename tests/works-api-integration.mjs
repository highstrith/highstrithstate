import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import net from 'node:net';
import { test } from 'node:test';

const root = path.resolve(import.meta.dirname, '..');
const mediaFields = ['video', 'poster', 'previewVideo', 'webVideo', 'mobileVideo'];
const fixtures = {
  original: 'assets/uploads/original.mp4',
  replacement: 'assets/uploads/replacement.mp4',
  poster: 'assets/uploads/posters/cover.jpg',
  preview: 'assets/optimized/uploaded/preview-abc123.mp4',
  web: 'assets/optimized/uploaded/web-abc123.mp4',
  mobile: 'assets/optimized/uploaded/mobile-abc123.mp4',
  uploadedPreview: 'assets/uploads/preview.mp4',
};
const uploaded = {
  id: 'uploaded', cnTitle: '原作品', enTitle: 'Original',
  video: fixtures.original, poster: fixtures.poster,
  previewVideo: fixtures.preview, webVideo: fixtures.web, mobileVideo: fixtures.mobile,
};
const builtIn = {
  ...uploaded, id: 'built-in', video: 'assets/works/built-in.mp4',
};

// Each case runs the unchanged server entry point in its own disposable directory.
// No test writes the real catalogue or touches the real asset tree.
async function withServer(works, run) {
  const directory = await fs.mkdtemp(path.join(os.tmpdir(), 'portfolio-works-api-'));
  let child;
  try {
    await fs.copyFile(path.join(root, 'serve.js'), path.join(directory, 'serve.js'));
    await fs.mkdir(path.join(directory, 'data'), { recursive: true });
    await fs.writeFile(path.join(directory, 'data/works.json'), JSON.stringify(works));
    for (const reference of [...Object.values(fixtures), builtIn.video]) {
      await fs.mkdir(path.dirname(path.join(directory, reference)), { recursive: true });
      await fs.writeFile(path.join(directory, reference), 'fixture media');
    }
    const socket = net.createServer();
    socket.listen(0, '127.0.0.1');
    await once(socket, 'listening');
    const port = socket.address().port;
    await new Promise((resolve, reject) => socket.close((error) => error ? reject(error) : resolve()));
    child = spawn(process.execPath, ['serve.js'], {
      cwd: directory, env: { ...process.env, PORT: String(port) }, stdio: ['ignore', 'pipe', 'pipe'],
    });
    let output = '';
    child.stdout.on('data', (chunk) => { output += chunk; });
    child.stderr.on('data', (chunk) => { output += chunk; });
    const base = `http://127.0.0.1:${port}`;
    for (let attempt = 0; attempt < 100; attempt++) {
      if (child.exitCode !== null) throw new Error(`Server exited: ${output}`);
      try {
        const response = await fetch(`${base}/api/works`);
        if (response.ok) break;
      } catch (_) {}
      if (attempt === 99) throw new Error(`Server did not start: ${output}`);
      await new Promise((resolve) => setTimeout(resolve, 20));
    }
    const request = async (method, endpoint = '/api/works', payload) => {
      const response = await fetch(`${base}${endpoint}`, {
        method,
        headers: payload === undefined ? {} : { 'Content-Type': 'application/json' },
        body: payload === undefined ? undefined : JSON.stringify(payload),
      });
      return { status: response.status, body: await response.json() };
    };
    await run({ request, directory });
  } finally {
    if (child && child.exitCode === null) {
      const exited = once(child, 'exit');
      child.kill('SIGTERM');
      await exited;
    }
    await fs.rm(directory, { recursive: true, force: true });
  }
}

test('GET preserves every stored derivative and defaults omitted derivatives to empty strings', async () => {
  await withServer([uploaded, { id: 'legacy', video: fixtures.original }], async ({ request }) => {
    const result = await request('GET');
    assert.equal(result.status, 200);
    assert.equal(result.body.works[0].previewVideo, fixtures.preview);
    assert.equal(result.body.works[0].webVideo, fixtures.web);
    assert.equal(result.body.works[0].mobileVideo, fixtures.mobile);
    for (const field of ['previewVideo', 'webVideo', 'mobileVideo']) {
      assert.equal(result.body.works[1][field], '', field);
    }
  });
});

test('POST persists optimized derivatives and PUT text edits retain all media', async () => {
  await withServer([], async ({ request }) => {
    const created = await request('POST', '/api/works', uploaded);
    assert.equal(created.status, 201);
    for (const field of mediaFields) assert.equal(created.body.work[field], uploaded[field], field);
    const changed = await request('PUT', `/api/works/${created.body.work.id}`, { cnTitle: '改名' });
    assert.equal(changed.status, 200);
    assert.equal(changed.body.work.cnTitle, '改名');
    for (const field of mediaFields) assert.equal(changed.body.work[field], uploaded[field], field);
    const stored = await request('GET');
    assert.equal(stored.body.works[0].webVideo, fixtures.web);
  });
});

test('POST accepts uploaded derivatives and PUT can change a derivative without replacing original', async () => {
  await withServer([], async ({ request }) => {
    const created = await request('POST', '/api/works', {
      video: fixtures.original, previewVideo: fixtures.uploadedPreview, webVideo: fixtures.uploadedPreview,
    });
    assert.equal(created.status, 201);
    assert.equal(created.body.work.previewVideo, fixtures.uploadedPreview);
    const changed = await request('PUT', `/api/works/${created.body.work.id}`, { previewVideo: fixtures.preview });
    assert.equal(changed.status, 200);
    assert.equal(changed.body.work.previewVideo, fixtures.preview);
    assert.equal(changed.body.work.webVideo, fixtures.uploadedPreview);
  });
});

test('replacing original invalidates all derivatives even when stale fields are resubmitted', async () => {
  await withServer([uploaded], async ({ request, directory }) => {
    const result = await request('PUT', '/api/works/uploaded', { ...uploaded, video: fixtures.replacement });
    assert.equal(result.status, 200);
    assert.equal(result.body.work.video, fixtures.replacement);
    assert.equal(result.body.work.poster, fixtures.poster);
    for (const field of ['previewVideo', 'webVideo', 'mobileVideo']) assert.equal(result.body.work[field], '', field);
    for (const reference of [fixtures.original, fixtures.preview, fixtures.web, fixtures.mobile]) {
      await assert.rejects(fs.access(path.join(directory, reference)), { code: 'ENOENT' });
    }
    await fs.access(path.join(directory, fixtures.poster));
  });
});

test('replacement preserves old uploaded original still referenced by another preview', async () => {
  await withServer([uploaded, { ...uploaded, id: 'shared', video: fixtures.replacement, previewVideo: fixtures.original }], async ({ request, directory }) => {
    assert.equal((await request('PUT', '/api/works/uploaded', { video: fixtures.replacement })).status, 200);
    await fs.access(path.join(directory, fixtures.original));
  });
});

test('deletion preserves resources referenced across all media fields and removes them after last reference', async () => {
  const references = {
    video: fixtures.poster, poster: fixtures.preview, previewVideo: fixtures.web,
    webVideo: fixtures.mobile, mobileVideo: fixtures.original,
  };
  await withServer([uploaded, { id: 'shared', ...references }], async ({ request, directory }) => {
    assert.equal((await request('DELETE', '/api/works/uploaded')).status, 200);
    for (const reference of Object.values(references)) await fs.access(path.join(directory, reference));
    assert.equal((await request('DELETE', '/api/works/shared')).status, 200);
    for (const reference of Object.values(references)) {
      await assert.rejects(fs.access(path.join(directory, reference)), { code: 'ENOENT' });
    }
  });
});

test('changing a derivative keeps a file still referenced by another field on the same work', async () => {
  await withServer([{ ...uploaded, previewVideo: fixtures.uploadedPreview, webVideo: fixtures.uploadedPreview }], async ({ request, directory }) => {
    assert.equal((await request('PUT', '/api/works/uploaded', { previewVideo: fixtures.preview })).status, 200);
    await fs.access(path.join(directory, fixtures.uploadedPreview));
  });
});

test('built-in text edits preserve all media while every media change and deletion remains forbidden', async () => {
  await withServer([builtIn], async ({ request }) => {
    const result = await request('PUT', '/api/works/built-in', { enTitle: 'Edited' });
    assert.equal(result.status, 200);
    for (const field of mediaFields) assert.equal(result.body.work[field], builtIn[field], field);
    for (const field of mediaFields) {
      const changed = await request('PUT', '/api/works/built-in', { [field]: fixtures.uploadedPreview });
      assert.equal(changed.status, 403, field);
    }
    assert.equal((await request('DELETE', '/api/works/built-in')).status, 403);
    assert.equal((await request('GET')).body.works.length, 1);
  });
});

test('text-only PUT preserves an existing missing derivative', async () => {
  await withServer([{ ...uploaded, webVideo: 'assets/optimized/uploaded/missing.mp4' }], async ({ request }) => {
    const result = await request('PUT', '/api/works/uploaded', { cnDesc: '只更新说明' });
    assert.equal(result.status, 200);
    assert.equal(result.body.work.webVideo, 'assets/optimized/uploaded/missing.mp4');
  });
});

test('an uploaded work with a missing original can still be deleted and cleaned up', async () => {
  await withServer([{ ...uploaded, video: 'assets/uploads/missing-original.mp4' }], async ({ request, directory }) => {
    assert.equal((await request('DELETE', '/api/works/uploaded')).status, 200);
    assert.equal((await request('GET')).body.works.length, 0);
    await assert.rejects(fs.access(path.join(directory, fixtures.preview)), { code: 'ENOENT' });
  });
});

test('POST and PUT reject directory traversal, sibling prefixes and symlink escapes', async () => {
  await withServer([uploaded], async ({ request, directory }) => {
    await fs.writeFile(path.join(directory, 'outside.mp4'), 'outside');
    await fs.mkdir(path.join(directory, 'assets/uploads-other'));
    await fs.writeFile(path.join(directory, 'assets/uploads-other/escape.mp4'), 'outside');
    await fs.symlink(path.join(directory, 'outside.mp4'), path.join(directory, 'assets/uploads/linked.mp4'));
    await fs.symlink(path.join(directory, 'outside.mp4'), path.join(directory, 'assets/optimized/uploaded/linked.mp4'));
    const invalidOriginals = [
      'assets/uploads/../../outside.mp4', 'assets/uploads/../uploads-other/escape.mp4',
      'assets/uploads/linked.mp4', fixtures.preview,
    ];
    for (const field of ['video', 'poster']) {
      for (const value of invalidOriginals) {
        assert.equal((await request('POST', '/api/works', { video: fixtures.original, [field]: value })).status, 400, `${field}: ${value}`);
        assert.equal((await request('PUT', '/api/works/uploaded', { [field]: value })).status, 400, `${field}: ${value}`);
      }
    }
    const invalidDerivatives = [
      'assets/optimized/../../outside.mp4', 'assets/uploads/../../outside.mp4',
      'assets/optimized/uploaded/linked.mp4', 'assets/uploads/linked.mp4',
      'assets/works/built-in.mp4', 'https://example.com/video.mp4',
    ];
    for (const field of ['previewVideo', 'webVideo', 'mobileVideo']) {
      for (const value of invalidDerivatives) {
        assert.equal((await request('POST', '/api/works', { video: fixtures.original, [field]: value })).status, 400, `${field}: ${value}`);
        assert.equal((await request('PUT', '/api/works/uploaded', { [field]: value })).status, 400, `${field}: ${value}`);
      }
    }
    assert.equal((await request('GET')).body.works.length, 1);
    assert.equal(await fs.readFile(path.join(directory, 'outside.mp4'), 'utf8'), 'outside');
  });
});

test('cleanup preserves shared files addressed through a safe relative alias', async () => {
  await withServer([uploaded, { ...uploaded, id: 'alias', video: fixtures.replacement, previewVideo: 'assets/optimized/uploaded/../uploaded/preview-abc123.mp4' }], async ({ request, directory }) => {
    assert.equal((await request('DELETE', '/api/works/uploaded')).status, 200);
    await fs.access(path.join(directory, fixtures.preview));
  });
});
