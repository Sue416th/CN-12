import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Settings, Heart, Clock, Award, ChevronRight, LogOut, MapPin, CalendarDays, User, Brain, Wallet, Activity, Users, Mountain, UserCheck } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

const menuItems = [
  { key: "favorites", icon: Heart, label: "Saved Favorites", desc: "Bookmarked attractions and culture stories", count: 12 },
  { key: "currentTrips", icon: CalendarDays, label: "Current Trips", desc: "Trip plans generated from your recent planning sessions", count: 3 },
  { key: "history", icon: Clock, label: "Travel History", desc: "Cities and places you've visited", count: 8 },
  { key: "achievements", icon: Award, label: "Travel Achievements", desc: "Badges you've unlocked", count: 5 },
  { key: "account", icon: Settings, label: "Account Settings", desc: "Manage your profile and preferences" },
];

const recentPlaces = [
  { name: "Dali Ancient Town", date: "Mar 10" },
  { name: "Erhai Park", date: "Mar 9" },
  { name: "Cangshan Cableway", date: "Mar 8" },
];

const Profile = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [activeSection, setActiveSection] = useState("account");
  const [userProfile, setUserProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const fetchUserProfile = async () => {
      try {
        const response = await fetch("http://localhost:3004/api/user/profile?user_id=1");
        if (response.ok) {
          const data = await response.json();
          setUserProfile(data.profile);
        }
      } catch (error) {
        console.error("Failed to fetch user profile:", error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchUserProfile();
  }, []);

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
                  { label: "Trips", value: "3" },
                  { label: "Visits", value: "12" },
                  { label: "Saved", value: "28" },
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
              {recentPlaces.map((place, i) => (
                <div key={i} className="flex items-center gap-3 text-sm">
                  <MapPin className="w-4 h-4 text-primary flex-shrink-0" />
                  <span className="flex-1">{place.name}</span>
                  <span className="text-xs text-muted-foreground">{place.date}</span>
                </div>
              ))}
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
            {menuItems.map((item, i) => (
              <button
                key={i}
                onClick={() => {
                  setActiveSection(item.key);
                  if (item.key === "account") {
                    navigate("/profile/settings");
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

          {/* User Profile Section */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="rounded-xl bg-card border border-border/50 shadow-sm overflow-hidden mt-5"
          >
            <div className="px-6 py-5 border-b border-border/30">
              <div className="flex items-center gap-3">
                <Brain className="w-5 h-5 text-primary" />
                <h3 className="font-display font-semibold">Your Travel Profile</h3>
              </div>
            </div>
            {loading ? (
              <div className="px-6 py-8">
                <div className="animate-pulse space-y-4">
                  <div className="h-4 bg-muted rounded w-1/2"></div>
                  <div className="h-4 bg-muted rounded w-3/4"></div>
                  <div className="h-4 bg-muted rounded w-1/3"></div>
                </div>
              </div>
            ) : userProfile ? (
              <div className="p-6 space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center flex-shrink-0">
                      <User className="w-5 h-5 text-primary" />
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Age Group</p>
                      <p className="font-medium">{userProfile.age_group || "Not specified"}</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center flex-shrink-0">
                      <Users className="w-5 h-5 text-primary" />
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Group Type</p>
                      <p className="font-medium">{userProfile.group_type || "Not specified"}</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center flex-shrink-0">
                      <Wallet className="w-5 h-5 text-primary" />
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Budget Level</p>
                      <p className="font-medium">{userProfile.budget_level || "Not specified"}</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center flex-shrink-0">
                      <Activity className="w-5 h-5 text-primary" />
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Fitness Level</p>
                      <p className="font-medium">{userProfile.fitness_level || "Not specified"}</p>
                    </div>
                  </div>
                </div>
                
                <div className="border-t border-border/30 pt-4">
                  <h4 className="font-medium mb-3">Interests</h4>
                  <div className="flex flex-wrap gap-2">
                    {userProfile.interests && userProfile.interests.length > 0 ? (
                      userProfile.interests.map((interest: string, index: number) => (
                        <span key={index} className="px-3 py-1 rounded-full bg-primary/10 text-primary text-sm">
                          {interest}
                        </span>
                      ))
                    ) : (
                      <span className="text-sm text-muted-foreground">No interests specified</span>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="px-6 py-8 text-center">
                <p className="text-muted-foreground">No profile data available</p>
              </div>
            )}
          </motion.div>

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
