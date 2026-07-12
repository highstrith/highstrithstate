const http = require("http");
const fs = require("fs");
const path = require("path");
const { URL } = require("url");

const root = __dirname;
const port = process.env.PORT || 3000;
const dataDir = path.join(root, "data");
const worksFile = path.join(dataDir, "works.json");
const uploadDir = path.join(root, "assets", "uploads");
const posterUploadDir = path.join(uploadDir, "posters");

const MAX_METADATA_BYTES = 256 * 1024;
const MAX_VIDEO_BYTES = 180 * 1024 * 1024;
const MAX_POSTER_BYTES = 12 * 1024 * 1024;

const types = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".webp": "image/webp",
  ".mp3": "audio/mpeg",
  ".mp4": "video/mp4",
  ".wav": "audio/wav",
};

const ALLOWED_VIDEO_EXTENSIONS = new Set([".mp4"]);
const ALLOWED_POSTER_EXTENSIONS = new Set([".png", ".jpg", ".jpeg", ".webp"]);

async function ensureStorage() {
  await fs.promises.mkdir(dataDir, { recursive: true });
  await fs.promises.mkdir(uploadDir, { recursive: true });
  await fs.promises.mkdir(posterUploadDir, { recursive: true });

  try {
    await fs.promises.access(worksFile, fs.constants.F_OK);
  } catch (_) {
    await fs.promises.writeFile(worksFile, "[]\n", "utf8");
  }
}

function sendJson(res, statusCode, payload) {
  const body = JSON.stringify(payload);
  res.writeHead(statusCode, {
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": "no-store",
    "Content-Length": Buffer.byteLength(body),
  });
  res.end(body);
}

function safeDecode(value) {
  try {
    return decodeURIComponent(value);
  } catch (_) {
    return value;
  }
}

function resolveInsideWorkspace(targetPath) {
  return path.resolve(targetPath);
}

function pathInsideWorkspace(targetPath) {
  return resolveInsideWorkspace(targetPath).startsWith(resolveInsideWorkspace(root));
}

function resolveFile(urlPath) {
  const clean = safeDecode(urlPath.split("?")[0].split("#")[0]);
  const relative = clean === "/" ? "/index.html" : clean;
  const full = path.join(root, relative);
  if (!pathInsideWorkspace(full)) return null;
  return full;
}

function sanitizeText(value, fallback, maxLength = 90) {
  const normalized = typeof value === "string" ? value.replace(/\s+/g, " ").trim() : "";
  return (normalized || fallback).slice(0, maxLength);
}

function toRelativeAssetPath(fullPath) {
  return path.relative(root, fullPath).replace(/\\/g, "/");
}

function uniqueStem(prefix) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function normalizeStoredWork(value) {
  const cnTitle = sanitizeText(value?.cnTitle, "Untitled Work", 80);
  const enTitle = sanitizeText(value?.enTitle, cnTitle || "Untitled Work", 80);
  const cnSub = sanitizeText(value?.cnSub, "", 64);
  const enSub = sanitizeText(value?.enSub, "", 64);

  return {
    id: sanitizeText(value?.id, uniqueStem("work"), 48),
    createdAt: typeof value?.createdAt === "string" ? value.createdAt : new Date().toISOString(),
    cnTitle,
    enTitle,
    cnSub,
    enSub,
    video: typeof value?.video === "string" ? value.video : "",
    mobileVideo: typeof value?.mobileVideo === "string" ? value.mobileVideo : "",
    poster: typeof value?.poster === "string" ? value.poster : "",
  };
}

async function readWorks() {
  try {
    const raw = await fs.promises.readFile(worksFile, "utf8");
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.map(normalizeStoredWork) : [];
  } catch (_) {
    return [];
  }
}

async function writeWorks(works) {
  await fs.promises.writeFile(worksFile, `${JSON.stringify(works, null, 2)}\n`, "utf8");
}

function isAllowedAssetReference(value, allowEmpty = false) {
  if (!value && allowEmpty) return true;
  if (typeof value !== "string") return false;
  if (!value.startsWith("assets/uploads/")) return false;

  const fullPath = path.join(root, value);
  return pathInsideWorkspace(fullPath);
}

function resolveAssetReference(value) {
  if (!isAllowedAssetReference(value, false)) return null;
  return resolveInsideWorkspace(path.join(root, value));
}

async function fileExists(fullPath) {
  try {
    await fs.promises.access(fullPath, fs.constants.F_OK);
    return true;
  } catch (_) {
    return false;
  }
}

async function deleteAssetIfUnused(assetRef, works, ignoredWorkId = "") {
  if (!assetRef) return;
  const inUse = works.some((work) => work.id !== ignoredWorkId
    && (work.video === assetRef || work.mobileVideo === assetRef || work.poster === assetRef));
  if (inUse) return;

  const fullPath = resolveAssetReference(assetRef);
  if (!fullPath || !(await fileExists(fullPath))) return;

  await fs.promises.unlink(fullPath).catch(() => {});
}

function readRequestBody(req, maxBytes) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    let total = 0;

    req.on("data", (chunk) => {
      total += chunk.length;
      if (total > maxBytes) {
        reject(new Error("BODY_TOO_LARGE"));
        req.destroy();
        return;
      }

      chunks.push(chunk);
    });

    req.on("end", () => resolve(Buffer.concat(chunks)));
    req.on("error", reject);
    req.on("aborted", () => reject(new Error("REQUEST_ABORTED")));
  });
}

async function parseJsonBody(req, res) {
  let payloadBuffer;

  try {
    payloadBuffer = await readRequestBody(req, MAX_METADATA_BYTES);
  } catch (error) {
    if (error.message === "BODY_TOO_LARGE") {
      sendJson(res, 413, { error: "Metadata payload is too large." });
      return null;
    }

    throw error;
  }

  try {
    return JSON.parse(payloadBuffer.toString("utf8"));
  } catch (_) {
    sendJson(res, 400, { error: "Metadata must be valid JSON." });
    return null;
  }
}

async function handleUpload(req, res, requestUrl) {
  const kind = requestUrl.searchParams.get("kind");
  const originalName = sanitizeText(requestUrl.searchParams.get("filename"), "", 120);
  const ext = path.extname(originalName).toLowerCase();

  if (kind !== "video" && kind !== "poster") {
    sendJson(res, 400, { error: "Unsupported upload kind." });
    return;
  }

  const allowedExtensions = kind === "video" ? ALLOWED_VIDEO_EXTENSIONS : ALLOWED_POSTER_EXTENSIONS;
  if (!allowedExtensions.has(ext)) {
    sendJson(res, 400, {
      error: kind === "video"
        ? "Only MP4 video uploads are supported."
        : "Poster images must be PNG, JPG, JPEG, or WEBP.",
    });
    return;
  }

  const maxBytes = kind === "video" ? MAX_VIDEO_BYTES : MAX_POSTER_BYTES;
  let body;

  try {
    body = await readRequestBody(req, maxBytes);
  } catch (error) {
    if (error.message === "BODY_TOO_LARGE") {
      sendJson(res, 413, {
        error: kind === "video"
          ? "Video is too large. Keep uploads under 180MB."
          : "Poster image is too large. Keep uploads under 12MB.",
      });
      return;
    }

    throw error;
  }

  if (!body.length) {
    sendJson(res, 400, { error: "Upload body was empty." });
    return;
  }

  const baseDir = kind === "video" ? uploadDir : posterUploadDir;
  const stem = uniqueStem(kind === "video" ? "work" : "poster");
  const fullPath = path.join(baseDir, `${stem}${ext}`);

  await fs.promises.writeFile(fullPath, body);

  sendJson(res, 201, {
    path: toRelativeAssetPath(fullPath),
  });
}

async function handleWorksGet(res) {
  const works = await readWorks();
  sendJson(res, 200, { works });
}

function buildWorkFromPayload(payload, existingWork = null) {
  return normalizeStoredWork({
    id: existingWork?.id || uniqueStem("work"),
    createdAt: existingWork?.createdAt || new Date().toISOString(),
    cnTitle: payload?.cnTitle ?? existingWork?.cnTitle,
    enTitle: payload?.enTitle ?? existingWork?.enTitle,
    cnSub: payload?.cnSub ?? existingWork?.cnSub,
    enSub: payload?.enSub ?? existingWork?.enSub,
    video: payload?.video ?? existingWork?.video,
    mobileVideo: payload?.mobileVideo ?? existingWork?.mobileVideo ?? "",
    poster: payload?.poster ?? existingWork?.poster ?? "",
  });
}

async function handleWorksPost(req, res) {
  const payload = await parseJsonBody(req, res);
  if (!payload) return;

  if (!isAllowedAssetReference(payload?.video)) {
    sendJson(res, 400, { error: "Video path is invalid." });
    return;
  }

  if (!isAllowedAssetReference(payload?.mobileVideo, true)) {
    sendJson(res, 400, { error: "Mobile video path is invalid." });
    return;
  }

  if (!isAllowedAssetReference(payload?.poster, true)) {
    sendJson(res, 400, { error: "Poster path is invalid." });
    return;
  }

  const work = buildWorkFromPayload(payload);
  const works = await readWorks();
  works.unshift(work);
  await writeWorks(works);

  sendJson(res, 201, { work });
}

async function handleWorksPut(req, res, workId) {
  const payload = await parseJsonBody(req, res);
  if (!payload) return;

  const works = await readWorks();
  const index = works.findIndex((item) => item.id === workId);
  if (index < 0) {
    sendJson(res, 404, { error: "Work not found." });
    return;
  }

  const existingWork = works[index];
  if (!isAllowedAssetReference(existingWork.video)) {
    sendJson(res, 403, { error: "Only uploaded works can be edited." });
    return;
  }

  const nextVideo = payload?.video ?? existingWork.video;
  const nextMobileVideo = payload?.mobileVideo ?? existingWork.mobileVideo ?? "";
  const nextPoster = payload?.poster ?? existingWork.poster ?? "";

  if (!isAllowedAssetReference(nextVideo)) {
    sendJson(res, 400, { error: "Video path is invalid." });
    return;
  }

  if (!isAllowedAssetReference(nextMobileVideo, true)) {
    sendJson(res, 400, { error: "Mobile video path is invalid." });
    return;
  }

  if (!isAllowedAssetReference(nextPoster, true)) {
    sendJson(res, 400, { error: "Poster path is invalid." });
    return;
  }

  const updatedWork = buildWorkFromPayload({
    ...payload,
    video: nextVideo,
    mobileVideo: nextMobileVideo,
    poster: nextPoster,
  }, existingWork);
  works[index] = updatedWork;
  await writeWorks(works);

  if (existingWork.video !== updatedWork.video) {
    await deleteAssetIfUnused(existingWork.video, works, updatedWork.id);
  }
  if (existingWork.mobileVideo !== updatedWork.mobileVideo) {
    await deleteAssetIfUnused(existingWork.mobileVideo, works, updatedWork.id);
  }
  if (existingWork.poster !== updatedWork.poster) {
    await deleteAssetIfUnused(existingWork.poster, works, updatedWork.id);
  }

  sendJson(res, 200, { work: updatedWork });
}

async function handleWorksDelete(res, workId) {
  const works = await readWorks();
  const index = works.findIndex((item) => item.id === workId);
  if (index < 0) {
    sendJson(res, 404, { error: "Work not found." });
    return;
  }

  const [removedWork] = works.splice(index, 1);
  if (!isAllowedAssetReference(removedWork.video)) {
    sendJson(res, 403, { error: "Only uploaded works can be deleted." });
    return;
  }

  await writeWorks(works);
  await deleteAssetIfUnused(removedWork.video, works, removedWork.id);
  await deleteAssetIfUnused(removedWork.mobileVideo, works, removedWork.id);
  await deleteAssetIfUnused(removedWork.poster, works, removedWork.id);

  sendJson(res, 200, { ok: true, id: workId });
}

async function handleApi(req, res, requestUrl) {
  if (req.method === "GET" && requestUrl.pathname === "/api/works") {
    await handleWorksGet(res);
    return true;
  }

  if (req.method === "POST" && requestUrl.pathname === "/api/upload-file") {
    await handleUpload(req, res, requestUrl);
    return true;
  }

  if (req.method === "POST" && requestUrl.pathname === "/api/works") {
    await handleWorksPost(req, res);
    return true;
  }

  const workMatch = requestUrl.pathname.match(/^\/api\/works\/([^/]+)$/);
  if (workMatch) {
    const workId = safeDecode(workMatch[1]);
    if (req.method === "PUT") {
      await handleWorksPut(req, res, workId);
      return true;
    }

    if (req.method === "DELETE") {
      await handleWorksDelete(res, workId);
      return true;
    }
  }

  return false;
}

function handleStatic(req, res, requestUrl) {
  const file = resolveFile(requestUrl.pathname || "/");
  if (!file) {
    res.writeHead(403);
    res.end("Forbidden");
    return;
  }

  fs.stat(file, (err, stat) => {
    if (err || !stat.isFile()) {
      res.writeHead(404);
      res.end("Not found");
      return;
    }

    const ext = path.extname(file).toLowerCase();
    const type = types[ext] || "application/octet-stream";
    const headers = {
      "Content-Type": type,
      "Cache-Control": "no-store",
    };
    const range = req.headers.range;
    const supportsRange = [".mp3", ".mp4", ".wav"].includes(ext);

    if (supportsRange) headers["Accept-Ranges"] = "bytes";

    if (supportsRange && range) {
      const match = range.match(/^bytes=(\d*)-(\d*)$/);
      if (!match) {
        res.writeHead(416, { ...headers, "Content-Range": `bytes */${stat.size}` });
        res.end();
        return;
      }

      const start = match[1] === "" ? 0 : Number(match[1]);
      const end = match[2] === "" ? stat.size - 1 : Number(match[2]);

      if (!Number.isInteger(start) || !Number.isInteger(end) || start > end || end >= stat.size) {
        res.writeHead(416, { ...headers, "Content-Range": `bytes */${stat.size}` });
        res.end();
        return;
      }

      res.writeHead(206, {
        ...headers,
        "Content-Length": end - start + 1,
        "Content-Range": `bytes ${start}-${end}/${stat.size}`,
      });

      fs.createReadStream(file, { start, end }).pipe(res);
      return;
    }

    res.writeHead(200, {
      ...headers,
      "Content-Length": stat.size,
    });

    fs.createReadStream(file).pipe(res);
  });
}

const storageReady = ensureStorage();

http.createServer(async (req, res) => {
  const requestUrl = new URL(req.url || "/", `http://${req.headers.host || `127.0.0.1:${port}`}`);

  try {
    await storageReady;

    if (await handleApi(req, res, requestUrl)) {
      return;
    }

    handleStatic(req, res, requestUrl);
  } catch (error) {
    console.error(error);
    sendJson(res, 500, { error: "Internal server error." });
  }
}).listen(port, () => {
  console.log(`Serving ${root} on http://localhost:${port}`);
});
