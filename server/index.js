import express from "express";
import path from "path";
import { fileURLToPath } from "url";
import { createProxyMiddleware } from "http-proxy-middleware";
import fetch from "node-fetch";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();

// Optional proxy to an existing backend (FastAPI) if provided
const BACKEND_URL = process.env.BACKEND_URL; // e.g., https://your-backend.onrender.com
console.log("BACKEND_URL=", BACKEND_URL || "<unset>");
if (BACKEND_URL) {
  app.use(
    "/api",
    createProxyMiddleware({
      target: BACKEND_URL,
      changeOrigin: true,
      pathRewrite: { "^/api": "/api" },
      xfwd: true,
      onProxyReq: (proxyReq) => {
        proxyReq.setHeader("X-Forwarded-Proto", "https");
      },
    })
  );
}

// Example local API route (can be removed if using proxy)
app.get("/api/hello", (req, res) => {
  res.json({ msg: "Hello World" });
});

// Debug route to test backend connectivity from the server
app.get("/api/_debug", async (req, res) => {
  try {
    if (!BACKEND_URL) return res.status(500).json({ error: "BACKEND_URL unset" });
    const url = `${BACKEND_URL}/api/placer/options`;
    const r = await fetch(url, { headers: { Accept: "application/json" } });
    const text = await r.text();
    res.json({ target: BACKEND_URL, status: r.status, body: text.slice(0, 500) });
  } catch (e) {
    res.status(500).json({ error: String(e) });
  }
});

// Serve frontend build (uses existing frontend directory)
const buildPath = path.join(__dirname, "../frontend/build");
app.use(express.static(buildPath));

app.get("*", (req, res) => {
  res.sendFile(path.join(buildPath, "index.html"));
});

const port = process.env.PORT || 5000;
app.listen(port, () => console.log(`Server running on port ${port}`)); 