import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Settings, Heart, Clock, ChevronRight, LogOut, MapPin, CalendarDays } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import axios from "axios";
import { getFavoriteItems, removeFavoriteDestination, type FavoriteItem } from "@/lib/favorites";

const menuItems = [
  { key: "favorites", icon: Heart, label: "Saved Favorites", desc: "Bookmarked attractions and culture stories", count: 12 },
  { key: "currentTrips", icon: CalendarDays, label: "Current Trips", desc: "Trip plans generated from your recent planning sessions" },
  { key: "history", icon: Clock, label: "Travel History", desc: "Cities and places you've visited", count: 8 },
  { key: "account", icon: Settings, label: "Account Settings", desc: "Manage your profile and preferences" },
];

type TripLike = {
  status?: string;
  itinerary?: unknown;
  city?: string;
  end_date?: string;
  updated_at?: string;
  created_at?: string;
};

type RecentPlace = {
  name: string;
  date: string;
};

const parseTripItinerary = (trip: TripLike) => {
  const raw = trip.itinerary;
  if (!raw) return null;
  if (typeof raw === "string") {
    try {
      return JSON.parse(raw) as { days?: Array<{ activities?: Array<{ name?: string }> }> };
    } catch {
      return null;
    }
  }
  if (typeof raw === "object") {
    return raw as { days?: Array<{ activities?: Array<{ name?: string }> }> };
  }
  return null;
};

const toDate = (value?: string) => {
  if (!value) return null;
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
};

const formatShortDate = (value?: string) => {
  const parsed = toDate(value);
  if (!parsed) return "--";
  return parsed.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
};

const countVisitedCities = (completedTrips: TripLike[]) => {
  const visitedCities = new Set<string>();
  completedTrips.forEach((trip) => {
    const city = String(trip.city || "").trim().toLowerCase();
    if (city) visitedCities.add(city);
  });
  return visitedCities.size > 0 ? visitedCities.size : completedTrips.length;
};

const buildRecentPlaces = (completedTrips: TripLike[]): RecentPlace[] => {
  const latestPlaceVisit = new Map<string, Date>();

  completedTrips.forEach((trip) => {
    const baseDate = toDate(trip.end_date) ?? toDate(trip.updated_at) ?? toDate(trip.created_at) ?? new Date();
    const itinerary = parseTripItinerary(trip);
    itinerary?.days?.forEach((day) => {
      day.activities?.forEach((activity) => {
        const name = String(activity?.name || "").trim();
        if (!name) return;
        const current = latestPlaceVisit.get(name);
        if (!current || baseDate > current) {
          latestPlaceVisit.set(name, baseDate);
        }
      });
    });
  });

  const recentFromActivities = Array.from(latestPlaceVisit.entries())
    .sort((a, b) => b[1].getTime() - a[1].getTime())
    .slice(0, 3)
    .map(([name, date]) => ({
      name,
      date: formatShortDate(date.toISOString()),
    }));

  if (recentFromActivities.length > 0) {
    return recentFromActivities;
  }

  return completedTrips
    .map((trip) => ({
      name: "Completed trip",
      date: formatShortDate(trip.end_date || trip.updated_at || trip.created_at),
    }))
    .slice(0, 3);
};

const Profile = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [activeSection, setActiveSection] = useState("account");
  const [tripCount, setTripCount] = useState(0);
  const [historyCount, setHistoryCount] = useState(0);
  const [visitCount, setVisitCount] = useState(0);
  const [favoriteItems, setFavoriteItems] = useState<FavoriteItem[]>([]);
  const [recentPlaces, setRecentPlaces] = useState<RecentPlace[]>([]);

  useEffect(() => {
    const fetchTripCount = async () => {
      if (!user || user.role !== "user") {
        setTripCount(0);
        setHistoryCount(0);
        setVisitCount(0);
        setRecentPlaces([]);
        return;
      }
      try {
        const response = await axios.get(`/api/trip/list?user_id=${user.id}`);
        if (response.data.success) {
          const allTrips = Array.isArray(response.data.trips) ? response.data.trips : [];
          const currentTrips = allTrips.filter((trip: { status?: string }) => String(trip.status || "").toLowerCase() !== "completed");
          const completedTrips = allTrips.filter((trip: { status?: string }) => String(trip.status || "").toLowerCase() === "completed");
          setTripCount(currentTrips.length);
          setHistoryCount(completedTrips.length);
          setVisitCount(countVisitedCities(completedTrips));
          setRecentPlaces(buildRecentPlaces(completedTrips));
        }
      } catch (_error) {
        setTripCount(0);
        setHistoryCount(0);
        setVisitCount(0);
        setRecentPlaces([]);
      }
    };

    void fetchTripCount();
  }, [user]);

  useEffect(() => {
    if (!user || user.role !== "user") {
      setFavoriteItems([]);
      return;
    }
    setFavoriteItems(getFavoriteItems(user.id));
  }, [user, activeSection]);

  const profileMenuItems = useMemo(
    () =>
      menuItems.map((item) => {
        if (item.key === "currentTrips") {
          return { ...item, count: tripCount };
        }
        if (item.key === "favorites") {
          return { ...item, count: favoriteItems.length };
        }
        if (item.key === "history") {
          return { ...item, count: historyCount };
        }
        return item;
      }),
    [tripCount, historyCount, favoriteItems.length],
  );

  return (
    <div className="container max-w-6xl mx-auto px-6 py-8">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Profile Card */}
        <div className="lg:col-span-1">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-xl bg-primary overflow-hidden"
          >
            <div className="p-6">
              <div className="flex items-center gap-4">
                <div className="w-20 h-20 rounded-full bg-primary-foreground/20 flex items-center justify-center text-3xl font-display text-primary-foreground">
                  {user?.name?.[0]?.toUpperCase() || "U"}
                </div>
                <div>
                  <h1 className="text-xl font-display font-bold text-primary-foreground">{user?.name || "Traveler"}</h1>
                  <p className="text-sm text-primary-foreground/70 mt-1">{user?.email || "traveler@example.com"}</p>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-3 mt-6">
                {[
                  { label: "Trips", value: String(tripCount) },
                  { label: "Visits", value: String(visitCount) },
                  { label: "Saved", value: String(favoriteItems.length) },
                ].map((stat, i) => (
                  <div key={i} className="text-center bg-primary-foreground/10 rounded-lg py-3">
                    <p className="text-xl font-bold text-primary-foreground">{stat.value}</p>
                    <p className="text-xs text-primary-foreground/70">{stat.label}</p>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>

          {/* Recent Places */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 }}
            className="rounded-xl bg-card border border-border/50 shadow-sm mt-5 p-5"
          >
            <h3 className="font-display font-semibold mb-3">Recently Visited</h3>
            <div className="space-y-3">
              {recentPlaces.length > 0 ? (
                recentPlaces.map((place, i) => (
                  <div key={`${place.name}-${i}`} className="flex items-center gap-3 text-sm">
                    <MapPin className="w-4 h-4 text-primary flex-shrink-0" />
                    <span className="flex-1">{place.name}</span>
                    <span className="text-xs text-muted-foreground">{place.date}</span>
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">No completed visits yet.</p>
              )}
            </div>
          </motion.div>
        </div>

        {/* Menu & Content */}
        <div className="lg:col-span-2">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="rounded-xl bg-card border border-border/50 shadow-sm overflow-hidden"
          >
            {profileMenuItems.map((item, i) => (
              <button
                key={i}
                onClick={() => {
                  setActiveSection(item.key);
                  if (item.key === "account") {
                    navigate("/profile/settings");
                    return;
                  }
                  if (item.key === "currentTrips") {
                    navigate("/trips");
                    return;
                  }
                  if (item.key === "history") {
                    navigate("/travel-history");
                    return;
                  }
                }}
                className="w-full flex items-center gap-4 px-6 py-5 border-b border-border/30 last:border-0 hover:bg-muted/50 transition-colors text-left"
              >
                <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <item.icon className="w-5 h-5 text-primary" />
                </div>
                <div className="flex-1">
                  <p className="font-medium">{item.label}</p>
                  <p className="text-sm text-muted-foreground">{item.desc}</p>
                </div>
                {item.count && (
                  <span className="text-sm text-muted-foreground font-medium">{item.count}</span>
                )}
                <ChevronRight
                  className={`w-4 h-4 transition-transform ${activeSection === item.key ? "text-primary translate-x-0.5" : "text-muted-foreground"}`}
                />
              </button>
            ))}
          </motion.div>

          {activeSection === "favorites" && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-5 rounded-xl bg-card border border-border/50 shadow-sm p-5"
            >
              <h3 className="font-display font-semibold mb-3">Saved Favorites</h3>
              {favoriteItems.length === 0 ? (
                <p className="text-sm text-muted-foreground">No saved attractions yet.</p>
              ) : (
                <div className="space-y-3">
                  {favoriteItems.map((item) => (
                    <div key={item.id} className="flex items-center gap-3 rounded-lg border border-border/50 p-3">
                      <img src={item.image} alt={item.name} className="w-16 h-16 rounded-md object-cover" />
                      <div className="flex-1">
                        <p className="text-sm font-medium">{item.name}</p>
                        <p className="text-xs text-muted-foreground">{item.location}</p>
                        <p className="text-xs text-muted-foreground mt-1">{item.shortDescription}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => navigate(`/destination/${item.id}`)}
                          className="text-xs px-2.5 py-1.5 rounded-md bg-primary text-primary-foreground"
                        >
                          View
                        </button>
                        <button
                          onClick={() => {
                            if (!user) return;
                            removeFavoriteDestination(user.id, item.id);
                            setFavoriteItems(getFavoriteItems(user.id));
                          }}
                          className="text-xs px-2.5 py-1.5 rounded-md border border-border text-muted-foreground"
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </motion.div>
          )}

          <motion.button
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            onClick={() => {
              logout();
              navigate("/");
            }}
            className="mt-5 w-full flex items-center justify-center gap-2 py-3 rounded-xl border border-border text-sm text-muted-foreground hover:bg-muted/50 transition-colors"
          >
            <LogOut className="w-4 h-4" />
            Sign Out
          </motion.button>
        </div>
      </div>
    </div>
  );
};

export default Profile;
