import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Users, Route, MessageSquare, CheckCircle2, Loader2, Pencil, Trash2, UserPlus } from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";

type AdminOverview = {
  storage: "database" | "file";
  totals: {
    users: number;
    trips: number;
    evaluations: number;
    completedTrips: number;
    completionRate: number;
  };
  tripsByStatus: Array<{ status: string; count: number }>;
  topCities: Array<{ city: string; count: number }>;
  sentimentDistribution: Array<{ sentiment: string; count: number }>;
  recentUsers: Array<{ id: number; name: string; email: string; role: string; created_at: string }>;
  recentTrips: Array<{ id: string; user_id: number; city: string; title: string; status: string; created_at: string }>;
  recentEvaluations: Array<{
    trip_id: string;
    user_id: number;
    trip_title: string;
    analysis: { sentiment?: string; summary?: string };
    updated_at?: string;
    created_at?: string;
  }>;
};

type AdminUser = {
  id: number;
  name: string;
  email: string;
  role: "user" | "admin";
  created_at?: string;
  updated_at?: string;
};

const METRIC_CARDS = [
  { key: "users", title: "Total Users", icon: Users },
  { key: "trips", title: "Total Trips", icon: Route },
  { key: "evaluations", title: "Total Evaluations", icon: MessageSquare },
  { key: "completionRate", title: "Completion Rate", icon: CheckCircle2 },
] as const;

const PIE_COLORS = ["#22c55e", "#0ea5e9", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4"];

const AdminDashboard = () => {
  const [data, setData] = useState<AdminOverview | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [usersLoading, setUsersLoading] = useState(true);
  const [userMessage, setUserMessage] = useState("");
  const [submittingUser, setSubmittingUser] = useState(false);
  const [editingUserId, setEditingUserId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState({ name: "", email: "", role: "user", password: "" });
  const [createForm, setCreateForm] = useState({ name: "", email: "", role: "user", password: "" });

  const readToken = () => localStorage.getItem("trailmark-auth-token");

  const fetchOverview = async (token: string) => {
    const response = await fetch("/api/admin/overview", {
      headers: { Authorization: `Bearer ${token}` },
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.message || "Failed to load dashboard data.");
    }
    return payload as AdminOverview;
  };

  const fetchUsers = async (token: string) => {
    setUsersLoading(true);
    try {
      const response = await fetch("/api/admin/users", {
        headers: { Authorization: `Bearer ${token}` },
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.message || "Failed to load users.");
      }
      setUsers(payload.users || []);
    } catch (err) {
      setUserMessage(err instanceof Error ? err.message : "Failed to load users.");
    } finally {
      setUsersLoading(false);
    }
  };

  useEffect(() => {
    const token = readToken();
    if (!token) {
      setError("Missing admin token. Please sign in again.");
      setLoading(false);
      return;
    }

    const load = async () => {
      try {
        const payload = await fetchOverview(token);
        setData(payload);
        await fetchUsers(token);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load dashboard data.");
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, []);

  const refreshAdminData = async () => {
    const token = readToken();
    if (!token) return;
    const payload = await fetchOverview(token);
    setData(payload);
    await fetchUsers(token);
  };

  const handleCreateUser = async () => {
    setUserMessage("");
    if (!createForm.name.trim() || !createForm.email.trim() || !createForm.password || !createForm.role) {
      setUserMessage("Please fill name, email, role and password.");
      return;
    }
    setSubmittingUser(true);
    try {
      const token = readToken();
      if (!token) throw new Error("Missing admin token.");
      const response = await fetch("/api/admin/users", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          name: createForm.name.trim(),
          email: createForm.email.trim(),
          role: createForm.role,
          password: createForm.password,
        }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.message || "Failed to create user.");
      setCreateForm({ name: "", email: "", role: "user", password: "" });
      setUserMessage("User created successfully.");
      await refreshAdminData();
    } catch (err) {
      setUserMessage(err instanceof Error ? err.message : "Failed to create user.");
    } finally {
      setSubmittingUser(false);
    }
  };

  const startEditUser = (user: AdminUser) => {
    setEditingUserId(user.id);
    setEditForm({ name: user.name, email: user.email, role: user.role, password: "" });
  };

  const handleSaveUser = async (userId: number) => {
    setUserMessage("");
    if (!editForm.name.trim() || !editForm.email.trim() || !editForm.role) {
      setUserMessage("Name, email and role are required.");
      return;
    }
    setSubmittingUser(true);
    try {
      const token = readToken();
      if (!token) throw new Error("Missing admin token.");
      const response = await fetch(`/api/admin/users/${userId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          name: editForm.name.trim(),
          email: editForm.email.trim(),
          role: editForm.role,
          password: editForm.password || undefined,
        }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.message || "Failed to update user.");
      setEditingUserId(null);
      setUserMessage("User updated.");
      await refreshAdminData();
    } catch (err) {
      setUserMessage(err instanceof Error ? err.message : "Failed to update user.");
    } finally {
      setSubmittingUser(false);
    }
  };

  const handleDeleteUser = async (userId: number) => {
    const ok = window.confirm("Delete this user? This action cannot be undone.");
    if (!ok) return;
    setSubmittingUser(true);
    setUserMessage("");
    try {
      const token = readToken();
      if (!token) throw new Error("Missing admin token.");
      const response = await fetch(`/api/admin/users/${userId}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.message || "Failed to delete user.");
      setUserMessage("User deleted.");
      await refreshAdminData();
    } catch (err) {
      setUserMessage(err instanceof Error ? err.message : "Failed to delete user.");
    } finally {
      setSubmittingUser(false);
    }
  };

  const cards = useMemo(() => {
    if (!data) return [];
    return METRIC_CARDS.map((item) => {
      if (item.key === "completionRate") {
        return { ...item, value: `${data.totals.completionRate}%` };
      }
      return { ...item, value: String(data.totals[item.key]) };
    });
  }, [data]);

  if (loading) {
    return (
      <div className="container max-w-6xl mx-auto px-6 py-16 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="container max-w-6xl mx-auto px-6 py-8">
        <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-5 text-sm text-destructive">
          {error}
        </div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="container max-w-7xl mx-auto px-6 py-8 space-y-6">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-2xl bg-primary text-primary-foreground p-7"
      >
        <h1 className="text-2xl font-display font-bold">Admin Console</h1>
        <p className="mt-2 text-sm text-primary-foreground/80">
          Real-time management view for users, trip data, and feedback analytics.
        </p>
        <p className="mt-1 text-xs text-primary-foreground/75">Storage mode: {data.storage}</p>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {cards.map((card, index) => (
          <motion.div
            key={card.title}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
            className="rounded-xl border border-border/50 bg-card p-4 shadow-sm"
          >
            <div className="flex items-center justify-between">
              <card.icon className="w-5 h-5 text-primary" />
              <p className="text-xl font-display font-semibold">{card.value}</p>
            </div>
            <p className="mt-2 text-sm text-muted-foreground">{card.title}</p>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="rounded-xl border border-border/50 bg-card p-5 shadow-sm">
          <h2 className="font-display font-semibold mb-4">Trips by Status</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.tripsByStatus}>
                <XAxis dataKey="status" />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="count" fill="#14b8a6" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="rounded-xl border border-border/50 bg-card p-5 shadow-sm">
          <h2 className="font-display font-semibold mb-4">Evaluation Sentiment</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={data.sentimentDistribution} dataKey="count" nameKey="sentiment" outerRadius={85} label>
                  {data.sentimentDistribution.map((item, index) => (
                    <Cell key={`${item.sentiment}-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-border/50 bg-card p-5 shadow-sm">
        <h2 className="font-display font-semibold mb-4">Top Cities by Trips</h2>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data.topCities}>
              <XAxis dataKey="city" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" fill="#3b82f6" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
        <div className="rounded-xl border border-border/50 bg-card p-5 shadow-sm xl:col-span-1">
          <h3 className="font-display font-semibold mb-3">User Management</h3>
          <div className="space-y-3">
            <div className="rounded-lg border border-border/60 p-3 space-y-2">
              <div className="text-sm font-medium inline-flex items-center gap-1.5">
                <UserPlus className="w-4 h-4 text-primary" />
                Create User
              </div>
              <input
                value={createForm.name}
                onChange={(e) => setCreateForm((prev) => ({ ...prev, name: e.target.value }))}
                placeholder="Name"
                className="w-full rounded-md border border-border bg-background px-2.5 py-1.5 text-sm"
              />
              <input
                value={createForm.email}
                onChange={(e) => setCreateForm((prev) => ({ ...prev, email: e.target.value }))}
                placeholder="Email"
                className="w-full rounded-md border border-border bg-background px-2.5 py-1.5 text-sm"
              />
              <div className="grid grid-cols-2 gap-2">
                <select
                  value={createForm.role}
                  onChange={(e) => setCreateForm((prev) => ({ ...prev, role: e.target.value }))}
                  className="rounded-md border border-border bg-background px-2.5 py-1.5 text-sm"
                >
                  <option value="user">user</option>
                  <option value="admin">admin</option>
                </select>
                <input
                  type="password"
                  value={createForm.password}
                  onChange={(e) => setCreateForm((prev) => ({ ...prev, password: e.target.value }))}
                  placeholder="Password"
                  className="rounded-md border border-border bg-background px-2.5 py-1.5 text-sm"
                />
              </div>
              <button
                onClick={handleCreateUser}
                disabled={submittingUser}
                className="w-full rounded-md bg-primary text-primary-foreground py-1.5 text-sm disabled:opacity-60"
              >
                Create User
              </button>
            </div>
            {userMessage && (
              <div className="text-xs rounded-md border border-border/60 bg-muted/30 px-2.5 py-2">
                {userMessage}
              </div>
            )}
            <div className="space-y-2 max-h-80 overflow-auto">
              {(usersLoading ? data.recentUsers : users).map((user) => (
                <div key={`${user.id}-${user.role}`} className="rounded-lg bg-muted/40 px-3 py-2">
                  {editingUserId === user.id ? (
                    <div className="space-y-2">
                      <input
                        value={editForm.name}
                        onChange={(e) => setEditForm((prev) => ({ ...prev, name: e.target.value }))}
                        className="w-full rounded-md border border-border bg-background px-2 py-1 text-xs"
                      />
                      <input
                        value={editForm.email}
                        onChange={(e) => setEditForm((prev) => ({ ...prev, email: e.target.value }))}
                        className="w-full rounded-md border border-border bg-background px-2 py-1 text-xs"
                      />
                      <div className="grid grid-cols-2 gap-2">
                        <select
                          value={editForm.role}
                          onChange={(e) => setEditForm((prev) => ({ ...prev, role: e.target.value }))}
                          className="rounded-md border border-border bg-background px-2 py-1 text-xs"
                        >
                          <option value="user">user</option>
                          <option value="admin">admin</option>
                        </select>
                        <input
                          type="password"
                          value={editForm.password}
                          onChange={(e) => setEditForm((prev) => ({ ...prev, password: e.target.value }))}
                          placeholder="New password (optional)"
                          className="rounded-md border border-border bg-background px-2 py-1 text-xs"
                        />
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleSaveUser(user.id)}
                          className="rounded-md bg-primary text-primary-foreground px-2 py-1 text-xs"
                        >
                          Save
                        </button>
                        <button
                          onClick={() => setEditingUserId(null)}
                          className="rounded-md border border-border px-2 py-1 text-xs"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <p className="text-sm font-medium">{user.name}</p>
                        <p className="text-xs text-muted-foreground">{user.email}</p>
                        <p className="text-xs text-muted-foreground mt-1">Role: {user.role}</p>
                      </div>
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => startEditUser(user)}
                          className="p-1.5 rounded-md hover:bg-muted"
                          title="Edit"
                        >
                          <Pencil className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => handleDeleteUser(user.id)}
                          className="p-1.5 rounded-md hover:bg-muted text-destructive"
                          title="Delete"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-border/50 bg-card p-5 shadow-sm xl:col-span-1">
          <h3 className="font-display font-semibold mb-3">Recent Trips</h3>
          <div className="space-y-2 max-h-72 overflow-auto">
            {data.recentTrips.map((trip) => (
              <div key={trip.id} className="rounded-lg bg-muted/40 px-3 py-2">
                <p className="text-sm font-medium">{trip.title || trip.id}</p>
                <p className="text-xs text-muted-foreground">City: {trip.city}</p>
                <p className="text-xs text-muted-foreground mt-1">Status: {trip.status}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-border/50 bg-card p-5 shadow-sm xl:col-span-1">
          <h3 className="font-display font-semibold mb-3">Recent Evaluations</h3>
          <div className="space-y-2 max-h-72 overflow-auto">
            {data.recentEvaluations.map((evaluation, index) => (
              <div key={`${evaluation.trip_id}-${index}`} className="rounded-lg bg-muted/40 px-3 py-2">
                <p className="text-sm font-medium">{evaluation.trip_title || evaluation.trip_id}</p>
                <p className="text-xs text-muted-foreground">
                  Sentiment: {evaluation.analysis?.sentiment || "unknown"}
                </p>
                <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                  {evaluation.analysis?.summary || "No summary"}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
