import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

export type UserRole = "user" | "admin";

type AuthUser = {
  id: number;
  name: string;
  email: string;
  role: UserRole;
};

type AuthResult = Promise<{ ok: boolean; message: string }>;

type AuthContextValue = {
  user: AuthUser | null;
  isLoggedIn: boolean;
  loading: boolean;
  login: (email: string, password: string, role: UserRole) => AuthResult;
  register: (name: string, email: string, password: string, role: UserRole) => AuthResult;
  refreshUser: () => Promise<void>;
  updateProfile: (name: string, email: string) => AuthResult;
  updatePassword: (currentPassword: string, newPassword: string) => AuthResult;
  logout: () => void;
};

const AUTH_USER_KEY = "trailmark-auth-user";
const AUTH_TOKEN_KEY = "trailmark-auth-token";

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const readStoredUser = (): AuthUser | null => {
  const raw = localStorage.getItem(AUTH_USER_KEY);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as AuthUser;
  } catch {
    return null;
  }
};

const readToken = () => localStorage.getItem(AUTH_TOKEN_KEY);

const saveToken = (token: string | null) => {
  if (!token) {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    return;
  }
  localStorage.setItem(AUTH_TOKEN_KEY, token);
};

const saveUser = (user: AuthUser | null) => {
  if (!user) {
    localStorage.removeItem(AUTH_USER_KEY);
    return;
  }

  localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
};

const requestJson = async (url: string, options?: RequestInit) => {
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
  });

  const data = await response.json().catch(() => ({}));
  return { response, data };
};

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<AuthUser | null>(() => readStoredUser());
  const [loading, setLoading] = useState(false);

  const refreshUser = async () => {
    const token = readToken();
    if (!token) {
      setUser(null);
      saveUser(null);
      return;
    }

    const { response, data } = await requestJson("/api/auth/me", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      saveToken(null);
      saveUser(null);
      setUser(null);
      return;
    }

    setUser(data.user);
    saveUser(data.user);
  };

  const login = async (email: string, password: string, role: UserRole) => {
    setLoading(true);
    try {
      const { response, data } = await requestJson("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({
          email: email.trim(),
          password,
          role,
        }),
      });

      if (!response.ok) {
        return { ok: false, message: data.message || "Login failed." };
      }

      saveToken(data.token);
      saveUser(data.user);
      setUser(data.user);
      return { ok: true, message: data.message || "Login successful." };
    } catch {
      return { ok: false, message: "Cannot reach authentication server." };
    } finally {
      setLoading(false);
    }
  };

  const register = async (name: string, email: string, password: string, role: UserRole) => {
    setLoading(true);
    try {
      const { response, data } = await requestJson("/api/auth/register", {
        method: "POST",
        body: JSON.stringify({
          name: name.trim(),
          email: email.trim(),
          password,
          role,
        }),
      });

      if (!response.ok) {
        return { ok: false, message: data.message || "Registration failed." };
      }

      saveToken(data.token);
      saveUser(data.user);
      setUser(data.user);
      return { ok: true, message: data.message || "Registration successful." };
    } catch {
      return { ok: false, message: "Cannot reach authentication server." };
    } finally {
      setLoading(false);
    }
  };

  const updateProfile = async (name: string, email: string) => {
    const token = readToken();
    if (!token) {
      return { ok: false, message: "Please login again." };
    }

    setLoading(true);
    try {
      const { response, data } = await requestJson("/api/auth/profile", {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          name: name.trim(),
          email: email.trim(),
        }),
      });

      if (!response.ok) {
        return { ok: false, message: data.message || "Failed to update profile." };
      }

      setUser(data.user);
      saveUser(data.user);
      return { ok: true, message: data.message || "Profile updated." };
    } catch {
      return { ok: false, message: "Cannot reach authentication server." };
    } finally {
      setLoading(false);
    }
  };

  const updatePassword = async (currentPassword: string, newPassword: string) => {
    const token = readToken();
    if (!token) {
      return { ok: false, message: "Please login again." };
    }

    setLoading(true);
    try {
      const { response, data } = await requestJson("/api/auth/password", {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          currentPassword,
          newPassword,
        }),
      });

      if (!response.ok) {
        return { ok: false, message: data.message || "Failed to update password." };
      }

      return { ok: true, message: data.message || "Password updated." };
    } catch {
      return { ok: false, message: "Cannot reach authentication server." };
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    saveToken(null);
    saveUser(null);
  };

  useEffect(() => {
    void refreshUser();
  }, []);

  const value = useMemo(
    () => ({
      user,
      isLoggedIn: !!user,
      loading,
      login,
      register,
      refreshUser,
      updateProfile,
      updatePassword,
      logout,
    }),
    [user, loading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
};
