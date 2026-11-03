// Framepick-only preview server. It serves reel/ as the site root, which is what
// the standalone repository looks like after the split (docs/framepick-repo-split-20261102.md).
// The portfolio's upload/admin API is intentionally absent: Framepick must not depend on it.
const http = require("http");
const fs = require("fs");
const path = require("path");
const { URL } = require("url");
const { createStaticHandler } = require("./server/static-site.cjs");
const { createAccountHandler } = require("./server/framepick-accounts.cjs");
const { createOrderHandler } = require("./server/framepick-orders.cjs");

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
const handleFramepickAccounts = createAccountHandler({});
// Demo orders: simulated payment only. FRAMEPICK_ORDERS_DATA_DIR isolates data
// for tests; the default lives outside the repository like the accounts store.
const handleFramepickOrders = createOrderHandler({ accounts: handleFramepickAccounts });
// The creator module is still an unshipped work in progress: mount it only when
// the file exists so a checkout without it still starts.
const creatorModule = path.join(root, "server", "framepick-creators.cjs");
const handleFramepickCreators = fs.existsSync(creatorModule)
  ? require(creatorModule).createCreatorHandler({ accounts: handleFramepickAccounts })
  : null;

http.createServer(async (req, res) => {
  const requestUrl = new URL(req.url || "/", `http://${req.headers.host || `127.0.0.1:${port}`}`);

  try {
    // Accounts own a narrower prefix: try them before the review handler, which
    // claims every /api/framepick path.
    if (await handleFramepickAccounts.handle(req, res, requestUrl)) return;
    // Orders own a narrower prefix too (demo goods, simulated payment).
    if (await handleFramepickOrders.handle(req, res, requestUrl)) return;
    // Creators own a narrower prefix: try them before the review handler, which
    // claims every /api/framepick path.
    if (handleFramepickCreators && await handleFramepickCreators.handle(req, res, requestUrl)) return;
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
