import { FormEvent, useMemo, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { LogIn, UserPlus, ShieldCheck, User as UserIcon } from "lucide-react";
import { useAuth, UserRole } from "@/context/AuthContext";

type AuthMode = "login" | "register";

const Auth = () => {
  const navigate = useNavigate();
  const { login, register, isLoggedIn, user, loading } = useAuth();

  const [mode, setMode] = useState<AuthMode>("login");
  const [role, setRole] = useState<UserRole>("user");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const pageTitle = useMemo(() => {
    if (mode === "login") {
      return "Sign In";
    }
    return "Create Account";
  }, [mode]);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError("");

    if (!email || !password || (mode === "register" && !name)) {
      setError("Please complete all required fields.");
      return;
    }

    const result =
      mode === "login"
        ? await login(email.trim(), password, role)
        : await register(name.trim(), email.trim(), password, role);

    if (!result.ok) {
      setError(result.message);
      return;
    }

    if (role === "admin") {
      navigate("/admin");
      return;
    }

    navigate("/");
  };

  if (isLoggedIn && user?.role === "user") {
    return <Navigate to="/" replace />;
  }

  if (isLoggedIn && user?.role === "admin") {
    return <Navigate to="/admin" replace />;
  }

  return (
    <div className="container max-w-6xl mx-auto px-6 py-10">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-md mx-auto rounded-2xl border border-border/50 bg-card shadow-sm p-7"
      >
        <h1 className="text-2xl font-display font-semibold">{pageTitle}</h1>
        <p className="text-sm text-muted-foreground mt-2">
          Sign in as a traveler to keep planning, or choose administrator access for the culture and tourism dashboard.
        </p>

        <div className="grid grid-cols-2 gap-2 mt-6">
          <button
            type="button"
            onClick={() => setMode("login")}
            className={`rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
              mode === "login" ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
            }`}
          >
            Login
          </button>
          <button
            type="button"
            onClick={() => setMode("register")}
            className={`rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
              mode === "register" ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
            }`}
          >
            Register
          </button>
        </div>

        <form onSubmit={handleSubmit} className="mt-5 space-y-4">
          {mode === "register" && (
            <div>
              <label className="text-sm font-medium">Name</label>
              <input
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder="Enter your display name"
                className="mt-1.5 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/20"
              />
            </div>
          )}

          <div>
            <label className="text-sm font-medium">Email</label>
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="name@example.com"
              className="mt-1.5 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/20"
            />
          </div>

          <div>
            <label className="text-sm font-medium">Password</label>
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Enter password"
              className="mt-1.5 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/20"
            />
          </div>

          <div>
            <p className="text-sm font-medium">Role</p>
            <div className="grid grid-cols-2 gap-2 mt-2">
              <button
                type="button"
                onClick={() => setRole("user")}
                className={`rounded-lg border px-3 py-2 text-sm transition-colors ${
                  role === "user"
                    ? "border-primary bg-primary/10 text-primary"
                    : "border-border text-muted-foreground hover:text-foreground"
                }`}
              >
                <span className="inline-flex items-center gap-1.5">
                  <UserIcon className="w-4 h-4" />
                  User Login
                </span>
              </button>
              <button
                type="button"
                onClick={() => setRole("admin")}
                className={`rounded-lg border px-3 py-2 text-sm transition-colors ${
                  role === "admin"
                    ? "border-primary bg-primary/10 text-primary"
                    : "border-border text-muted-foreground hover:text-foreground"
                }`}
              >
                <span className="inline-flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4" />
                  Admin Login
                </span>
              </button>
            </div>
          </div>

          {error && <p className="text-sm text-destructive">{error}</p>}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-primary text-primary-foreground py-2.5 text-sm font-medium hover:opacity-95 transition-opacity inline-flex items-center justify-center gap-2"
          >
            {mode === "login" ? <LogIn className="w-4 h-4" /> : <UserPlus className="w-4 h-4" />}
            {loading ? "Processing..." : mode === "login" ? "Continue" : "Create and Continue"}
          </button>
        </form>
      </motion.div>
    </div>
  );
};

export default Auth;
