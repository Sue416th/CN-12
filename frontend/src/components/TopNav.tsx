import { MapPin, Compass, BookOpen, User, ShieldCheck, LogOut } from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

const TopNav = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { isLoggedIn, user, logout } = useAuth();

  const navItems = [
    { path: "/", label: "Trip Planner", icon: MapPin },
    { path: "/navigate", label: "Live Navigation", icon: Compass },
    { path: "/culture", label: "Culture", icon: BookOpen },
    ...(isLoggedIn
      ? user?.role === "admin"
        ? [{ path: "/admin", label: "Admin Console", icon: ShieldCheck }]
        : [{ path: "/profile", label: "Profile", icon: User }]
      : [{ path: "/auth", label: "Sign In / Register", icon: User }]),
  ];

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-card/80 backdrop-blur-xl">
      <div className="container flex items-center justify-between h-16 max-w-6xl mx-auto px-6">
        <button onClick={() => navigate("/")} className="flex items-center gap-2">
          <Compass className="w-6 h-6 text-primary" />
          <span className="text-lg font-display font-bold text-foreground">TrailMark</span>
        </button>
        <nav className="flex items-center gap-1">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            const Icon = item.icon;
            return (
              <button
                key={item.path}
                onClick={() => navigate(item.path)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted"
                }`}
              >
                <Icon className="w-4 h-4" />
                {item.label}
              </button>
            );
          })}
          {isLoggedIn && (
            <button
              onClick={() => {
                logout();
                navigate("/");
              }}
              className="ml-1 flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
            >
              <LogOut className="w-4 h-4" />
              Sign Out
            </button>
          )}
        </nav>
      </div>
    </header>
  );
};

export default TopNav;
