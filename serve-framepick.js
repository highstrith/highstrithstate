// Framepick-only preview server. It serves reel/ as the site root, which is what
// the standalone repository looks like after the split (docs/framepick-repo-split-20261102.md).
// The portfolio's upload/admin API is intentionally absent: Framepick must not depend on it.
const http = require("http");
const fs = require("fs");
const path = require("path");
const { URL } = require("url");
const { createStaticHandler } = require("./server/static-site.cjs");

const root = __dirname;
const siteRoot = path.join(root, "reel");
const port = Number(process.env.PORT || 3100);
const indexPath = path.join(siteRoot, "index.html");
const reviewModule = path.join(root, "server", "framepick-reviews.cjs");

function readFilmIds() {
  if (!fs.existsSync(indexPath)) return [];
  return [...fs.readFileSync(indexPath, "utf8")
    .matchAll(/<article\b[^>]*data-film="([^"]+)"/g)].map((match) => match[1]);
}

const handleFramepickReviews = fs.existsSync(reviewModule)
  ? require(reviewModule).createReviewHandler({
      dataDir: process.env.FRAMEPICK_REVIEWS_DATA_DIR,
      filmIds: readFilmIds(),
    })
  : null;

const handleStatic = createStaticHandler({ root: siteRoot });

http.createServer(async (req, res) => {
  const requestUrl = new URL(req.url || "/", `http://${req.headers.host || `127.0.0.1:${port}`}`);

  try {
    if (handleFramepickReviews && await handleFramepickReviews(req, res, requestUrl)) return;
    handleStatic(req, res, requestUrl);
  } catch (error) {
    console.error(error);
    res.writeHead(500, { "Content-Type": "application/json; charset=utf-8" });
    res.end(JSON.stringify({ error: "Internal server error." }));
  }
}).listen(port, () => {
  const films = readFilmIds().length;
  console.log(`Framepick on http://localhost:${port} (site root ${siteRoot}, ${films} films, reviews API ${handleFramepickReviews ? "on" : "off"})`);
});
