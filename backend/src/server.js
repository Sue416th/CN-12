import express from "express";
import cors from "cors";
import bcrypt from "bcryptjs";
import dotenv from "dotenv";
import fs from "fs/promises";
import { fileURLToPath } from "url";
import { pool, checkDbConnection } from "./db.js";
import { signToken } from "./auth.js";
import { requireAuth, requireAdmin } from "./middleware.js";

dotenv.config();

const app = express();
const PORT = Number(process.env.PORT || 3001);
const HOST = process.env.HOST || "127.0.0.1";
const AUTH_FILE_PATH = fileURLToPath(new URL("../auth_users.json", import.meta.url));
const TRIPS_FILE_PATH = fileURLToPath(new URL("../trips_data.json", import.meta.url));
const EVALUATIONS_FILE_PATH = fileURLToPath(new URL("../trip_evaluations_data.json", import.meta.url));

app.use(
  cors({
    origin: ["http://localhost:8080", "http://127.0.0.1:8080", "http://localhost:8081", "http://127.0.0.1:8081"],
  }),
);
app.use(express.json());

const isDatabaseAvailable = async () => {
  try {
    await checkDbConnection();
    return true;
  } catch (_error) {
    return false;
  }
};

const readAuthStore = async () => {
  try {
    const raw = await fs.readFile(AUTH_FILE_PATH, "utf8");
    const parsed = JSON.parse(raw);
    const users = Array.isArray(parsed.users) ? parsed.users : [];
    const nextId = Number(parsed.nextId || users.length + 1);
    return { users, nextId };
  } catch (_error) {
    return { users: [], nextId: 1 };
  }
};

const writeAuthStore = async (store) => {
  const normalizedStore = {
    users: Array.isArray(store.users) ? store.users : [],
    nextId: Number(store.nextId || 1),
  };
  await fs.writeFile(AUTH_FILE_PATH, `${JSON.stringify(normalizedStore, null, 2)}\n`, "utf8");
};

const fileSafeUser = (user) => ({
  id: user.id,
  name: user.name,
  email: user.email,
  role: user.role,
});

const readJsonFileObject = async (path) => {
  try {
    const raw = await fs.readFile(path, "utf8");
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch (_error) {
    return {};
  }
};

const toIsoString = (value) => {
  if (!value) return "";
  if (typeof value === "string") return value;
  if (value instanceof Date) return value.toISOString();
  if (typeof value === "object" && typeof value.toISOString === "function") return value.toISOString();
  return String(value);
};

const buildAdminOverview = ({ users, trips, evaluations }) => {
  const tripsByStatusMap = new Map();
  const cityCountMap = new Map();
  const sentimentMap = new Map();

  for (const trip of trips) {
    const status = String(trip.status || "Unknown");
    tripsByStatusMap.set(status, (tripsByStatusMap.get(status) || 0) + 1);
    const city = String(trip.city || "Unknown");
    cityCountMap.set(city, (cityCountMap.get(city) || 0) + 1);
  }

  for (const item of evaluations) {
    const sentiment = String(item.analysis?.sentiment || "unknown");
    sentimentMap.set(sentiment, (sentimentMap.get(sentiment) || 0) + 1);
  }

  const completedTrips = trips.filter((trip) => String(trip.status || "").toLowerCase() === "completed").length;
  const completionRate = trips.length > 0 ? Number(((completedTrips / trips.length) * 100).toFixed(1)) : 0;

  const tripsByStatus = Array.from(tripsByStatusMap.entries())
    .map(([status, count]) => ({ status, count }))
    .sort((a, b) => b.count - a.count);
  const topCities = Array.from(cityCountMap.entries())
    .map(([city, count]) => ({ city, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 8);
  const sentimentDistribution = Array.from(sentimentMap.entries())
    .map(([sentiment, count]) => ({ sentiment, count }))
    .sort((a, b) => b.count - a.count);

  const recentUsers = [...users]
    .sort((a, b) => new Date(toIsoString(b.created_at)).getTime() - new Date(toIsoString(a.created_at)).getTime())
    .slice(0, 8);
  const recentTrips = [...trips]
    .sort((a, b) => new Date(toIsoString(b.created_at)).getTime() - new Date(toIsoString(a.created_at)).getTime())
    .slice(0, 10);
  const recentEvaluations = [...evaluations]
    .sort((a, b) => new Date(toIsoString(b.updated_at || b.created_at)).getTime() - new Date(toIsoString(a.updated_at || a.created_at)).getTime())
    .slice(0, 10);

  return {
    totals: {
      users: users.length,
      trips: trips.length,
      evaluations: evaluations.length,
      completedTrips,
      completionRate,
    },
    tripsByStatus,
    topCities,
    sentimentDistribution,
    recentUsers,
    recentTrips,
    recentEvaluations,
  };
};

const getAdminDataFromDatabase = async () => {
  const [userRows] = await pool.query(
    "SELECT id, name, email, role, created_at FROM users ORDER BY created_at DESC LIMIT 1000",
  );
  const [tripRows] = await pool.query(
    "SELECT id, user_id, city, title, days, status, created_at, updated_at FROM trips ORDER BY created_at DESC LIMIT 2000",
  );
  const [evaluationRows] = await pool.query(
    "SELECT trip_id, user_id, trip_title, feedback, analysis, created_at, updated_at FROM trip_evaluations ORDER BY updated_at DESC LIMIT 2000",
  );

  const users = userRows.map((row) => ({
    ...row,
    created_at: toIsoString(row.created_at),
  }));
  const trips = tripRows.map((row) => ({
    ...row,
    created_at: toIsoString(row.created_at),
    updated_at: toIsoString(row.updated_at),
  }));
  const evaluations = evaluationRows.map((row) => ({
    ...row,
    feedback: row.feedback ? (typeof row.feedback === "string" ? JSON.parse(row.feedback) : row.feedback) : {},
    analysis: row.analysis ? (typeof row.analysis === "string" ? JSON.parse(row.analysis) : row.analysis) : {},
    created_at: toIsoString(row.created_at),
    updated_at: toIsoString(row.updated_at),
  }));

  return { users, trips, evaluations };
};

const getAdminDataFromFileStore = async () => {
  const authStore = await readAuthStore();
  const tripsObject = await readJsonFileObject(TRIPS_FILE_PATH);
  const evaluationsObject = await readJsonFileObject(EVALUATIONS_FILE_PATH);

  const users = authStore.users.map((user) => ({
    id: user.id,
    name: user.name,
    email: user.email,
    role: user.role,
    created_at: toIsoString(user.created_at),
  }));
  const trips = Object.values(tripsObject).map((trip) => ({
    id: trip.id,
    user_id: trip.user_id,
    city: trip.city,
    title: trip.title,
    days: trip.days,
    status: trip.status,
    created_at: toIsoString(trip.created_at),
    updated_at: toIsoString(trip.updated_at),
  }));
  const evaluations = Object.values(evaluationsObject).map((item) => ({
    trip_id: item.trip_id,
    user_id: item.user_id,
    trip_title: item.trip_title,
    feedback: item.feedback || {},
    analysis: item.analysis || {},
    created_at: toIsoString(item.created_at),
    updated_at: toIsoString(item.updated_at),
  }));

  return { users, trips, evaluations };
};

const getAdminUsersFromDatabase = async () => {
  const [rows] = await pool.query(
    "SELECT id, name, email, role, created_at, updated_at FROM users ORDER BY created_at DESC LIMIT 2000",
  );
  return rows.map((row) => ({
    ...row,
    created_at: toIsoString(row.created_at),
    updated_at: toIsoString(row.updated_at),
  }));
};

const getAdminUsersFromFileStore = async () => {
  const store = await readAuthStore();
  return store.users
    .map((user) => ({
      id: Number(user.id),
      name: String(user.name || ""),
      email: String(user.email || ""),
      role: String(user.role || "user"),
      created_at: toIsoString(user.created_at),
      updated_at: toIsoString(user.updated_at),
    }))
    .sort((a, b) => Number(b.id) - Number(a.id));
};

app.get("/api/health", async (_req, res) => {
  const dbAvailable = await isDatabaseAvailable();
  return res.json({
    ok: true,
    storage: dbAvailable ? "database" : "file",
  });
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
    const dbAvailable = await isDatabaseAvailable();
    const nextName = String(name).trim();
    const nextEmail = String(email).trim();
    const passwordHash = await bcrypt.hash(String(password), 10);
    let user;

    if (dbAvailable) {
      const [existingRows] = await pool.query(
        "SELECT id FROM users WHERE email = ? AND role = ? LIMIT 1",
        [nextEmail, role],
      );

      if (existingRows.length > 0) {
        return res.status(409).json({ message: "This account already exists for the selected role." });
      }

      const [insertResult] = await pool.query(
        "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
        [nextName, nextEmail, passwordHash, role],
      );

      user = {
        id: insertResult.insertId,
        name: nextName,
        email: nextEmail,
        role,
      };
    } else {
      const store = await readAuthStore();
      const existingUser = store.users.find((item) => item.email === nextEmail && item.role === role);
      if (existingUser) {
        return res.status(409).json({ message: "This account already exists for the selected role." });
      }

      const createdAt = new Date().toISOString();
      const newUser = {
        id: store.nextId,
        name: nextName,
        email: nextEmail,
        role,
        password_hash: passwordHash,
        created_at: createdAt,
        updated_at: createdAt,
      };
      store.users.push(newUser);
      store.nextId += 1;
      await writeAuthStore(store);
      user = fileSafeUser(newUser);
    }

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
    const dbAvailable = await isDatabaseAvailable();
    const nextEmail = String(email).trim();
    let account;

    if (dbAvailable) {
      const [rows] = await pool.query(
        "SELECT id, name, email, password_hash, role FROM users WHERE email = ? AND role = ? LIMIT 1",
        [nextEmail, role],
      );
      account = rows[0];
    } else {
      const store = await readAuthStore();
      account = store.users.find((item) => item.email === nextEmail && item.role === role);
    }

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
    const dbAvailable = await isDatabaseAvailable();
    let user;
    if (dbAvailable) {
      const [rows] = await pool.query(
        "SELECT id, name, email, role FROM users WHERE id = ? LIMIT 1",
        [req.auth.id],
      );
      user = rows[0];
    } else {
      const store = await readAuthStore();
      const row = store.users.find((item) => Number(item.id) === Number(req.auth.id));
      user = row ? fileSafeUser(row) : null;
    }

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
    const dbAvailable = await isDatabaseAvailable();
    if (dbAvailable) {
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
    }

    const store = await readAuthStore();
    const currentUser = store.users.find((item) => Number(item.id) === Number(req.auth.id));
    if (!currentUser) {
      return res.status(404).json({ message: "User not found" });
    }

    const duplicateUser = store.users.find(
      (item) => item.email === nextEmail && item.role === currentUser.role && Number(item.id) !== Number(req.auth.id),
    );
    if (duplicateUser) {
      return res.status(409).json({ message: "This email is already used in your current role." });
    }

    currentUser.name = nextName;
    currentUser.email = nextEmail;
    currentUser.updated_at = new Date().toISOString();
    await writeAuthStore(store);

    return res.json({
      message: "Account profile updated.",
      user: fileSafeUser(currentUser),
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
    const dbAvailable = await isDatabaseAvailable();
    if (dbAvailable) {
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
    }

    const store = await readAuthStore();
    const user = store.users.find((item) => Number(item.id) === Number(req.auth.id));
    if (!user) {
      return res.status(404).json({ message: "User not found" });
    }

    const matches = await bcrypt.compare(String(currentPassword), user.password_hash);
    if (!matches) {
      return res.status(401).json({ message: "Current password is incorrect." });
    }

    user.password_hash = await bcrypt.hash(String(newPassword), 10);
    user.updated_at = new Date().toISOString();
    await writeAuthStore(store);

    return res.json({ message: "Password updated successfully." });
  } catch (error) {
    return res.status(500).json({ message: "Failed to update password", error: String(error) });
  }
});

app.get("/api/admin/overview", requireAuth, requireAdmin, async (_req, res) => {
  try {
    const dbAvailable = await isDatabaseAvailable();
    const data = dbAvailable ? await getAdminDataFromDatabase() : await getAdminDataFromFileStore();
    const overview = buildAdminOverview(data);

    return res.json({
      storage: dbAvailable ? "database" : "file",
      ...overview,
    });
  } catch (error) {
    return res.status(500).json({ message: "Failed to load admin dashboard data", error: String(error) });
  }
});

app.get("/api/admin/users", requireAuth, requireAdmin, async (_req, res) => {
  try {
    const dbAvailable = await isDatabaseAvailable();
    const users = dbAvailable ? await getAdminUsersFromDatabase() : await getAdminUsersFromFileStore();
    return res.json({ users, total: users.length, storage: dbAvailable ? "database" : "file" });
  } catch (error) {
    return res.status(500).json({ message: "Failed to load users", error: String(error) });
  }
});

app.post("/api/admin/users", requireAuth, requireAdmin, async (req, res) => {
  const { name, email, password, role } = req.body || {};
  const nextName = String(name || "").trim();
  const nextEmail = String(email || "").trim();
  const nextRole = String(role || "").trim();
  const nextPassword = String(password || "");

  if (!nextName || !nextEmail || !nextRole || !nextPassword) {
    return res.status(400).json({ message: "name, email, role, password are required" });
  }
  if (!["user", "admin"].includes(nextRole)) {
    return res.status(400).json({ message: "role must be user or admin" });
  }
  if (nextPassword.length < 6) {
    return res.status(400).json({ message: "Password must be at least 6 characters." });
  }

  try {
    const dbAvailable = await isDatabaseAvailable();
    const passwordHash = await bcrypt.hash(nextPassword, 10);
    if (dbAvailable) {
      const [existingRows] = await pool.query(
        "SELECT id FROM users WHERE email = ? AND role = ? LIMIT 1",
        [nextEmail, nextRole],
      );
      if (existingRows.length > 0) {
        return res.status(409).json({ message: "User already exists for the selected role." });
      }

      const [insertResult] = await pool.query(
        "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
        [nextName, nextEmail, passwordHash, nextRole],
      );
      const [rows] = await pool.query(
        "SELECT id, name, email, role, created_at, updated_at FROM users WHERE id = ? LIMIT 1",
        [insertResult.insertId],
      );
      const user = rows[0];
      return res.status(201).json({
        message: "User created.",
        user: {
          ...user,
          created_at: toIsoString(user.created_at),
          updated_at: toIsoString(user.updated_at),
        },
      });
    }

    const store = await readAuthStore();
    const duplicate = store.users.find((item) => item.email === nextEmail && item.role === nextRole);
    if (duplicate) {
      return res.status(409).json({ message: "User already exists for the selected role." });
    }

    const now = new Date().toISOString();
    const createdUser = {
      id: store.nextId,
      name: nextName,
      email: nextEmail,
      role: nextRole,
      password_hash: passwordHash,
      created_at: now,
      updated_at: now,
    };
    store.users.push(createdUser);
    store.nextId += 1;
    await writeAuthStore(store);
    return res.status(201).json({ message: "User created.", user: fileSafeUser(createdUser) });
  } catch (error) {
    return res.status(500).json({ message: "Failed to create user", error: String(error) });
  }
});

app.put("/api/admin/users/:id", requireAuth, requireAdmin, async (req, res) => {
  const userId = Number(req.params.id);
  const { name, email, role, password } = req.body || {};
  const nextName = typeof name === "string" ? name.trim() : "";
  const nextEmail = typeof email === "string" ? email.trim() : "";
  const nextRole = typeof role === "string" ? role.trim() : "";
  const nextPassword = typeof password === "string" ? password : "";

  if (!userId || !nextName || !nextEmail || !nextRole) {
    return res.status(400).json({ message: "id, name, email, role are required" });
  }
  if (!["user", "admin"].includes(nextRole)) {
    return res.status(400).json({ message: "role must be user or admin" });
  }
  if (nextPassword && nextPassword.length < 6) {
    return res.status(400).json({ message: "Password must be at least 6 characters." });
  }

  try {
    const dbAvailable = await isDatabaseAvailable();
    if (dbAvailable) {
      const [targetRows] = await pool.query("SELECT id FROM users WHERE id = ? LIMIT 1", [userId]);
      if (targetRows.length === 0) {
        return res.status(404).json({ message: "User not found" });
      }

      const [duplicateRows] = await pool.query(
        "SELECT id FROM users WHERE email = ? AND role = ? AND id <> ? LIMIT 1",
        [nextEmail, nextRole, userId],
      );
      if (duplicateRows.length > 0) {
        return res.status(409).json({ message: "Another user already uses this email for the selected role." });
      }

      if (nextPassword) {
        const passwordHash = await bcrypt.hash(nextPassword, 10);
        await pool.query(
          "UPDATE users SET name = ?, email = ?, role = ?, password_hash = ? WHERE id = ?",
          [nextName, nextEmail, nextRole, passwordHash, userId],
        );
      } else {
        await pool.query(
          "UPDATE users SET name = ?, email = ?, role = ? WHERE id = ?",
          [nextName, nextEmail, nextRole, userId],
        );
      }

      const [rows] = await pool.query(
        "SELECT id, name, email, role, created_at, updated_at FROM users WHERE id = ? LIMIT 1",
        [userId],
      );
      const user = rows[0];
      return res.json({
        message: "User updated.",
        user: {
          ...user,
          created_at: toIsoString(user.created_at),
          updated_at: toIsoString(user.updated_at),
        },
      });
    }

    const store = await readAuthStore();
    const targetUser = store.users.find((item) => Number(item.id) === userId);
    if (!targetUser) {
      return res.status(404).json({ message: "User not found" });
    }
    const duplicate = store.users.find(
      (item) => item.email === nextEmail && item.role === nextRole && Number(item.id) !== userId,
    );
    if (duplicate) {
      return res.status(409).json({ message: "Another user already uses this email for the selected role." });
    }

    targetUser.name = nextName;
    targetUser.email = nextEmail;
    targetUser.role = nextRole;
    if (nextPassword) {
      targetUser.password_hash = await bcrypt.hash(nextPassword, 10);
    }
    targetUser.updated_at = new Date().toISOString();
    await writeAuthStore(store);
    return res.json({ message: "User updated.", user: fileSafeUser(targetUser) });
  } catch (error) {
    return res.status(500).json({ message: "Failed to update user", error: String(error) });
  }
});

app.delete("/api/admin/users/:id", requireAuth, requireAdmin, async (req, res) => {
  const userId = Number(req.params.id);
  if (!userId) {
    return res.status(400).json({ message: "Valid user id is required" });
  }
  if (Number(req.auth?.id) === userId) {
    return res.status(400).json({ message: "You cannot delete your own admin account." });
  }

  try {
    const dbAvailable = await isDatabaseAvailable();
    if (dbAvailable) {
      const [result] = await pool.query("DELETE FROM users WHERE id = ? LIMIT 1", [userId]);
      if (!result.affectedRows) {
        return res.status(404).json({ message: "User not found" });
      }
      return res.json({ message: "User deleted." });
    }

    const store = await readAuthStore();
    const before = store.users.length;
    store.users = store.users.filter((item) => Number(item.id) !== userId);
    if (store.users.length === before) {
      return res.status(404).json({ message: "User not found" });
    }
    await writeAuthStore(store);
    return res.json({ message: "User deleted." });
  } catch (error) {
    return res.status(500).json({ message: "Failed to delete user", error: String(error) });
  }
});

app.listen(PORT, HOST, () => {
  console.log(`Auth API running on http://${HOST}:${PORT}`);
});

app.get("/", (_req, res) => {
  res.json({
    name: "Trailmark API",
    version: "1.0.0",
    endpoints: {
      health: "/api/health",
      auth: {
        register: "POST /api/auth/register",
        login: "POST /api/auth/login",
        me: "GET /api/auth/me",
        profile: "PUT /api/auth/profile",
        password: "PUT /api/auth/password",
      },
      admin: {
        overview: "GET /api/admin/overview",
        users: "GET /api/admin/users",
      },
    },
  });
});
