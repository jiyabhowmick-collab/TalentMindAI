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
const path = require("path");
dotenv.config({ path: path.join(__dirname, ".env") });

const connectDB = require("./config/db");
const authRoutes = require("./routes/auth.routes");
const profileRoutes = require("./routes/profile.routes");
const historyRoutes = require("./routes/history.routes");
const { verifyMailer } = require("./utils/mailer.util");

// Establish connection to the MongoDB database
connectDB();

// Check if the email service configuration is valid before starting up
verifyMailer();

// Initialize the Express application
const app = express();
const PORT = process.env.PORT || 4000;

// Setup global middleware (CORS, body parsing, cookies)
app.use(cors({
  origin: process.env.CORS_ORIGIN,
  credentials: true,
}));
app.use(express.json({ limit: "50mb" }));
app.use(cookieParser());

// Register core API routes
app.use("/api/auth", authRoutes);
app.use("/api/profile", profileRoutes);
app.use("/api/history", historyRoutes);

// Setup proxy handlers to communicate with the Python Flask ranking engine
const multer  = require("multer");
const axios   = require("axios");
const FormData = require("form-data");
const jwt_decode = require("jsonwebtoken");
const RankingHistory = require("./models/RankingHistory");

const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 600 * 1024 * 1024 }, // 600 MB
});

const PYTHON_URL = process.env.PYTHON_URL;

// Handle the candidate CSV upload and kick off the AI ranking pipeline in Flask
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

    // Automatically fetch and save the resulting CSVs to the user's MongoDB profile
    try {
      let userId = null;
      const authHeader = req.headers.authorization;
      if (authHeader?.startsWith("Bearer")) {
        const token = authHeader.split(" ")[1];
        const decoded = jwt_decode.verify(token, process.env.JWT_SECRET);
        userId = decoded.id;
      } else if (req.cookies?.access_token) {
        const decoded = jwt_decode.verify(req.cookies.access_token, process.env.JWT_SECRET);
        userId = decoded.id;
      }

      if (userId && response.data.job_id) {
        const jobId = response.data.job_id;
        const jdText = req.body.job_description || "";
        const firstLine = jdText.split("\n").map(l => l.trim()).find(l => l.length > 0) || "Untitled Job";

        await RankingHistory.findOneAndUpdate(
          { userId, jobId },
          {
            userId,
            jobId,
            jobTitle: firstLine.slice(0, 100),
            jobDescriptionSnippet: jdText.slice(0, 500),
            totalCandidates: response.data.total_candidates || 0,
            returnedCandidates: response.data.returned || 0,
            fileName: req.file.originalname || "",
          },
          { upsert: true, returnDocument: 'after', setDefaultsOnInsert: true }
        );
        console.log(`[upload] Saved ranking history skeleton for user ${userId}`);
      }
    } catch (historyErr) {
      // Non-blocking: don't fail the upload if history save fails
      console.warn(`[upload] Failed to save history:`, historyErr.message);
    }

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
    const jobId = req.params.jobId;
    console.log(`[results] Fetching job ${jobId}`);
    const response = await axios.get(`${PYTHON_URL}/results/${jobId}`);
    console.log(`[results] job=${jobId} returned=${response.data.returned}`);

    // Automatically fetch and save the resulting CSVs to the user's MongoDB profile
    try {
      const csvData = {};
      for (const tier of [10, 50, 100]) {
        try {
          const csvRes = await axios.get(`${PYTHON_URL}/export/${jobId}/${tier}`, {
            responseType: "text",
            timeout: 30000,
          });
          csvData[`csvTop${tier}`] = csvRes.data;
        } catch (csvErr) {
          console.warn(`[results] Failed to fetch CSV tier ${tier}:`, csvErr.message);
        }
      }

      await RankingHistory.findOneAndUpdate(
        { jobId },
        {
          totalCandidates: response.data.total_candidates || 0,
          returnedCandidates: response.data.returned || 0,
          ...csvData,
        },
        { returnDocument: 'after' }
      );
      console.log(`[results] Saved ranking history + CSVs for job ${jobId}`);
    } catch (historyErr) {
      console.warn(`[results] Failed to save history/CSVs:`, historyErr.message);
    }

    res.json(response.data);
  } catch (err) {
    const status = err.response?.status || 404;
    console.error(`[results] ERROR ${status} for job ${req.params.jobId}:`, err.message);
    res.status(status).json({ error: "Not found" });
  }
});

// Poll pipeline progress (step 1–5) for granular frontend updates
app.get("/api/status/:jobId", async (req, res) => {
  try {
    const response = await axios.get(`${PYTHON_URL}/status/${req.params.jobId}`);
    res.json(response.data);
  } catch (err) {
    const status = err.response?.status || 404;
    console.error(`[status] ERROR ${status} for job ${req.params.jobId}:`, err.message);
    res.status(status).json({ error: "Not found" });
  }
});

// Stream CSV export for a given job ID and tier (10 / 50 / 100)
// Tries Flask first (live cache), then falls back to MongoDB (persisted)
app.get("/api/export/:jobId/:tier", async (req, res) => {
  const { jobId, tier } = req.params;
  const tierNum = parseInt(tier, 10);

  if (![10, 50, 100].includes(tierNum)) {
    return res.status(400).json({ error: "Tier must be 10, 50, or 100" });
  }

  const filename = `talent-mind_top-${tierNum}_${jobId.slice(0, 8)}.csv`;

  // 1) Try Flask first (job might still be cached)
  try {
    console.log(`[export] Trying Flask: job=${jobId} tier=${tierNum}`);
    const response = await axios.get(
      `${PYTHON_URL}/export/${jobId}/${tierNum}`,
      { responseType: "stream", timeout: 10000 }
    );
    res.setHeader("Content-Type", "text/csv");
    res.setHeader("Content-Disposition", `attachment; filename=${filename}`);
    response.data.pipe(res);
    return;
  } catch (flaskErr) {
    console.log(`[export] Flask miss, trying MongoDB: ${flaskErr.message}`);
  }

  // 2) Fall back to MongoDB
  try {
    const csvField = `csvTop${tierNum}`;
    // Find in any user's history (export is by jobId, not user-specific)
    const entry = await RankingHistory.findOne(
      { jobId, [csvField]: { $ne: "" } },
      { [csvField]: 1 }
    ).lean();

    if (!entry || !entry[csvField]) {
      return res.status(404).json({ error: "CSV not found. The ranking may have expired." });
    }

    res.setHeader("Content-Type", "text/csv");
    res.setHeader("Content-Disposition", `attachment; filename=${filename}`);
    res.send(entry[csvField]);
  } catch (dbErr) {
    console.error(`[export] MongoDB error:`, dbErr.message);
    res.status(500).json({ error: "Failed to retrieve CSV." });
  }
});

// Basic health check endpoint
app.get("/api/health", (_req, res) => {
  res.json({
    status: "ok",
    service: "talentmind-server",
    port: PORT,
  });
});

// Catch-all global error handler
app.use((err, _req, res, _next) => {
  console.error("[server] Unhandled error:", err.message);
  res.status(500).json({ success: false, error: err.message });
});

// Start listening for incoming requests
app.listen(PORT, () => {
  console.log(`[server] TalentMind server listening on port ${PORT}`);
});
