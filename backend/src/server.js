import express from "express";
import cors from "cors";
import bcrypt from "bcryptjs";
import dotenv from "dotenv";
import { pool, checkDbConnection } from "./db.js";
import { signToken } from "./auth.js";
import { requireAuth } from "./middleware.js";

dotenv.config();

const app = express();
const PORT = Number(process.env.PORT || 3001);

app.use(
  cors({
    origin: ["http://localhost:8080", "http://127.0.0.1:8080"],
  }),
);
app.use(express.json());

app.get("/api/health", async (_req, res) => {
  try {
    await checkDbConnection();
    return res.json({ ok: true });
  } catch (error) {
    return res.status(500).json({ ok: false, message: "Database unavailable", error: String(error) });
  }
});

app.post("/api/auth/register", async (req, res) => {
  const { name, email, password, role } = req.body || {};

  if (!name || !email || !password || !role) {
    return res.status(400).json({ message: "name, email, password, role are required" });
  }

  if (!["user", "admin"].includes(role)) {
    return res.status(400).json({ message: "role must be user or admin" });
  }

  if (String(password).length < 6) {
    return res.status(400).json({ message: "Password must be at least 6 characters." });
  }

  try {
    const [existingRows] = await pool.query(
      "SELECT id FROM users WHERE email = ? AND role = ? LIMIT 1",
      [String(email).trim(), role],
    );

    if (existingRows.length > 0) {
      return res.status(409).json({ message: "This account already exists for the selected role." });
    }

    const passwordHash = await bcrypt.hash(String(password), 10);

    const [insertResult] = await pool.query(
      "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
      [String(name).trim(), String(email).trim(), passwordHash, role],
    );

    const user = {
      id: insertResult.insertId,
      name: String(name).trim(),
      email: String(email).trim(),
      role,
    };

    const token = signToken({
      id: user.id,
      email: user.email,
      role: user.role,
    });

    return res.status(201).json({
      message: "Registration successful.",
      token,
      user,
    });
  } catch (error) {
    return res.status(500).json({ message: "Failed to register", error: String(error) });
  }
});

app.post("/api/auth/login", async (req, res) => {
  const { email, password, role } = req.body || {};

  if (!email || !password || !role) {
    return res.status(400).json({ message: "email, password, role are required" });
  }

  try {
    const [rows] = await pool.query(
      "SELECT id, name, email, password_hash, role FROM users WHERE email = ? AND role = ? LIMIT 1",
      [String(email).trim(), role],
    );

    const account = rows[0];
    if (!account) {
      return res.status(401).json({ message: "Invalid credentials or role selection." });
    }

    const ok = await bcrypt.compare(String(password), account.password_hash);
    if (!ok) {
      return res.status(401).json({ message: "Invalid credentials or role selection." });
    }

    const user = {
      id: account.id,
      name: account.name,
      email: account.email,
      role: account.role,
    };

    const token = signToken({
      id: user.id,
      email: user.email,
      role: user.role,
    });

    return res.json({
      message: "Login successful.",
      token,
      user,
    });
  } catch (error) {
    return res.status(500).json({ message: "Failed to login", error: String(error) });
  }
});

app.get("/api/auth/me", requireAuth, async (req, res) => {
  try {
    const [rows] = await pool.query(
      "SELECT id, name, email, role FROM users WHERE id = ? LIMIT 1",
      [req.auth.id],
    );

    const user = rows[0];
    if (!user) {
      return res.status(404).json({ message: "User not found" });
    }

    return res.json({ user });
  } catch (error) {
    return res.status(500).json({ message: "Failed to fetch user", error: String(error) });
  }
});

app.put("/api/auth/profile", requireAuth, async (req, res) => {
  const { name, email } = req.body || {};
  const nextName = String(name || "").trim();
  const nextEmail = String(email || "").trim();

  if (!nextName || !nextEmail) {
    return res.status(400).json({ message: "name and email are required" });
  }

  try {
    const [currentRows] = await pool.query(
      "SELECT id, role FROM users WHERE id = ? LIMIT 1",
      [req.auth.id],
    );

    const currentUser = currentRows[0];
    if (!currentUser) {
      return res.status(404).json({ message: "User not found" });
    }

    const [duplicateRows] = await pool.query(
      "SELECT id FROM users WHERE email = ? AND role = ? AND id <> ? LIMIT 1",
      [nextEmail, currentUser.role, req.auth.id],
    );

    if (duplicateRows.length > 0) {
      return res.status(409).json({ message: "This email is already used in your current role." });
    }

    await pool.query(
      "UPDATE users SET name = ?, email = ? WHERE id = ?",
      [nextName, nextEmail, req.auth.id],
    );

    const [rows] = await pool.query(
      "SELECT id, name, email, role FROM users WHERE id = ? LIMIT 1",
      [req.auth.id],
    );

    return res.json({
      message: "Account profile updated.",
      user: rows[0],
    });
  } catch (error) {
    return res.status(500).json({ message: "Failed to update profile", error: String(error) });
  }
});

app.put("/api/auth/password", requireAuth, async (req, res) => {
  const { currentPassword, newPassword } = req.body || {};

  if (!currentPassword || !newPassword) {
    return res.status(400).json({ message: "currentPassword and newPassword are required" });
  }

  if (String(newPassword).length < 6) {
    return res.status(400).json({ message: "New password must be at least 6 characters." });
  }

  try {
    const [rows] = await pool.query(
      "SELECT id, password_hash FROM users WHERE id = ? LIMIT 1",
      [req.auth.id],
    );

    const user = rows[0];
    if (!user) {
      return res.status(404).json({ message: "User not found" });
    }

    const matches = await bcrypt.compare(String(currentPassword), user.password_hash);
    if (!matches) {
      return res.status(401).json({ message: "Current password is incorrect." });
    }

    const passwordHash = await bcrypt.hash(String(newPassword), 10);
    await pool.query(
      "UPDATE users SET password_hash = ? WHERE id = ?",
      [passwordHash, req.auth.id],
    );

    return res.json({ message: "Password updated successfully." });
  } catch (error) {
    return res.status(500).json({ message: "Failed to update password", error: String(error) });
  }
});

app.listen(PORT, () => {
  console.log(`Auth API running on http://localhost:${PORT}`);
});
