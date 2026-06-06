/**
 * server.js - Main Express entry point for TalentMind.
 *
 * Runs on port 4000 (configurable via .env).
 * Connects to MongoDB Atlas, sets up JWT auth, proxies ranking to Flask.
 */

const express = require("express");
const cors = require("cors");
const dotenv = require("dotenv");
const cookieParser = require("cookie-parser");

// Load environment variables FIRST
dotenv.config();

const connectDB = require("./config/db");
const authRoutes = require("./routes/auth.routes");
const profileRoutes = require("./routes/profile.routes");
const { verifyMailer } = require("./utils/mailer.util");

// ── Connect to MongoDB ──────────────────────────────────────────────
connectDB();

// ── Verify mailer on startup ─────────────────────────────────────────
verifyMailer();

// ── App ─────────────────────────────────────────────────────────────
const app = express();
const PORT = process.env.PORT || 4000;

// ── Middleware ───────────────────────────────────────────────────────
app.use(cors({
  origin: process.env.CORS_ORIGIN || "http://localhost:3000",
  credentials: true,
}));
app.use(express.json({ limit: "50mb" }));
app.use(cookieParser());

// ── Routes ──────────────────────────────────────────────────────────
app.use("/api/auth", authRoutes);
app.use("/api/profile", profileRoutes);

// ── Ranking proxy ───────────────────────────────────────────────────
const multer  = require("multer");
const axios   = require("axios");
const FormData = require("form-data");

const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 600 * 1024 * 1024 }, // 600 MB
});

const PYTHON_URL = process.env.PYTHON_URL || "http://localhost:5000";

// Upload candidates + JD → trigger ranking
app.post("/api/upload", upload.single("file"), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: "No file received by Node" });
    }
    console.log(`[upload] file="${req.file.originalname}" size=${(req.file.size / 1024 / 1024).toFixed(2)}MB jd_length=${(req.body.job_description || "").length}chars`);

    const form = new FormData();
    form.append("file", req.file.buffer, {
      filename:    req.file.originalname,
      contentType: req.file.mimetype,
      knownLength: req.file.size,
    });
    form.append("job_description", req.body.job_description || "");

    console.log(`[upload] Forwarding to Flask at ${PYTHON_URL}/rank ...`);
    const response = await axios.post(`${PYTHON_URL}/rank`, form, {
      headers:        form.getHeaders(),
      maxBodyLength:  Infinity,
      timeout:        350000,
    });
    console.log(`[upload] Flask responded: job_id=${response.data.job_id} returned=${response.data.returned}`);
    res.json(response.data);
  } catch (err) {
    const status = err.response?.status || 500;
    const detail = err.response?.data || err.message;
    console.error(`[upload] ERROR ${status}:`, detail);
    res.status(status).json({ error: typeof detail === "string" ? detail : JSON.stringify(detail) });
  }
});

// Poll ranked results by job ID
app.get("/api/results/:jobId", async (req, res) => {
  try {
    console.log(`[results] Fetching job ${req.params.jobId}`);
    const response = await axios.get(`${PYTHON_URL}/results/${req.params.jobId}`);
    console.log(`[results] job=${req.params.jobId} returned=${response.data.returned}`);
    res.json(response.data);
  } catch (err) {
    const status = err.response?.status || 404;
    console.error(`[results] ERROR ${status} for job ${req.params.jobId}:`, err.message);
    res.status(status).json({ error: "Not found" });
  }
});

// Stream CSV export for a given job ID and tier (10 / 50 / 100)
app.get("/api/export/:jobId/:tier", async (req, res) => {
  try {
    console.log(`[export] job=${req.params.jobId} tier=${req.params.tier}`);
    const response = await axios.get(
      `${PYTHON_URL}/export/${req.params.jobId}/${req.params.tier}`,
      { responseType: "stream" }
    );
    res.setHeader("Content-Type", "text/csv");
    res.setHeader("Content-Disposition", response.headers["content-disposition"]);
    response.data.pipe(res);
  } catch (err) {
    console.error(`[export] ERROR:`, err.message);
    res.status(500).json({ error: err.message });
  }
});

// ── Health check ────────────────────────────────────────────────────
app.get("/api/health", (_req, res) => {
  res.json({
    status: "ok",
    service: "talentmind-server",
    port: PORT,
  });
});

// ── Global error handler ────────────────────────────────────────────
app.use((err, _req, res, _next) => {
  console.error("[server] Unhandled error:", err.message);
  res.status(500).json({ success: false, error: err.message });
});

// ── Start ───────────────────────────────────────────────────────────
app.listen(PORT, () => {
  console.log(`[server] TalentMind server listening on http://localhost:${PORT}`);
});
