import { useEffect, useState, type FormEvent } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, Save, Lock } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

const ProfileSettings = () => {
  const navigate = useNavigate();
  const { user, updateProfile, updatePassword, loading } = useAuth();

  const [name, setName] = useState(user?.name || "");
  const [email, setEmail] = useState(user?.email || "");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    setName(user?.name || "");
    setEmail(user?.email || "");
  }, [user?.name, user?.email]);

  const handleProfileSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    setMessage("");

    if (!name.trim() || !email.trim()) {
      setError("Name and email cannot be empty.");
      return;
    }

    const result = await updateProfile(name, email);
    if (!result.ok) {
      setError(result.message);
      return;
    }

    setMessage(result.message);
  };

  const handlePasswordSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    setMessage("");

    if (!currentPassword || !newPassword || !confirmPassword) {
      setError("Please complete all password fields.");
      return;
    }

    if (newPassword !== confirmPassword) {
      setError("New password and confirm password do not match.");
      return;
    }

    const result = await updatePassword(currentPassword, newPassword);
    if (!result.ok) {
      setError(result.message);
      return;
    }

    setCurrentPassword("");
    setNewPassword("");
    setConfirmPassword("");
    setMessage(result.message);
  };

  return (
    <div className="container max-w-6xl mx-auto px-6 py-8">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-xl border border-border/50 bg-card p-6 shadow-sm"
      >
        <button
          onClick={() => navigate("/profile")}
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Profile
        </button>

        <h1 className="text-2xl font-display font-semibold mt-4">Account Settings</h1>
        <p className="text-sm text-muted-foreground mt-2">
          Edit your profile information and password. Changes are synced to MySQL immediately.
        </p>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
          <form className="rounded-xl border border-border/50 p-5 space-y-4" onSubmit={handleProfileSubmit}>
            <h2 className="font-display font-semibold">Profile Information</h2>

            <div>
              <label className="text-sm font-medium">Name</label>
              <input
                value={name}
                onChange={(event) => setName(event.target.value)}
                className="mt-1.5 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/20"
                placeholder="Enter your name"
              />
            </div>

            <div>
              <label className="text-sm font-medium">Email</label>
              <input
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                className="mt-1.5 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/20"
                placeholder="name@example.com"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="rounded-lg bg-primary text-primary-foreground px-4 py-2 text-sm font-medium hover:opacity-95 transition-opacity disabled:opacity-70 inline-flex items-center gap-2"
            >
              <Save className="w-4 h-4" />
              {loading ? "Saving..." : "Save Profile"}
            </button>
          </form>

          <form className="rounded-xl border border-border/50 p-5 space-y-4" onSubmit={handlePasswordSubmit}>
            <h2 className="font-display font-semibold">Password & Security</h2>

            <div>
              <label className="text-sm font-medium">Current Password</label>
              <input
                type="password"
                value={currentPassword}
                onChange={(event) => setCurrentPassword(event.target.value)}
                className="mt-1.5 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/20"
                placeholder="Enter current password"
              />
            </div>

            <div>
              <label className="text-sm font-medium">New Password</label>
              <input
                type="password"
                value={newPassword}
                onChange={(event) => setNewPassword(event.target.value)}
                className="mt-1.5 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/20"
                placeholder="At least 6 characters"
              />
            </div>

            <div>
              <label className="text-sm font-medium">Confirm New Password</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
                className="mt-1.5 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/20"
                placeholder="Re-enter new password"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="rounded-lg border border-border px-4 py-2 text-sm font-medium hover:bg-muted/50 transition-colors disabled:opacity-70 inline-flex items-center gap-2"
            >
              <Lock className="w-4 h-4" />
              {loading ? "Updating..." : "Update Password"}
            </button>
          </form>
        </div>

        {error && <p className="text-sm text-destructive mt-5">{error}</p>}
        {message && <p className="text-sm text-primary mt-5">{message}</p>}
      </motion.div>
    </div>
  );
};

export default ProfileSettings;
