import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { Plus, MapPin, Sparkles, Heart } from "lucide-react";
import heroImg from "@/assets/hero-travel.jpg";
import fallbackImage from "@/assets/destination-1.jpg";
import { useAuth } from "@/context/AuthContext";
import { DESTINATIONS } from "@/lib/destinations";
import { isFavoriteDestination, toggleFavoriteDestination } from "@/lib/favorites";

const FALLBACK_IMAGE = fallbackImage;

const Index = () => {
  const navigate = useNavigate();
  const { isLoggedIn, user } = useAuth();
  const [, setFavoriteRefreshTick] = useState(0);

  const scenicHighlights = useMemo(() => DESTINATIONS.slice(0, 6), []);
  const popularPicks = useMemo(() => DESTINATIONS.slice(0, 3), []);

  const handleCreateTrip = () => {
    if (!isLoggedIn) {
      alert("Please sign in first to generate a trip.");
      navigate("/auth");
      return;
    }
    navigate("/trip-planner");
  };

  const handleDestinationClick = (destinationId: string) => {
    navigate(`/destination/${destinationId}`);
  };

  const handleToggleFavorite = (destinationId: string) => {
    const destination = DESTINATIONS.find((item) => item.id === destinationId);
    if (!destination) return;
    if (!isLoggedIn || !user || user.role !== "user") {
      alert("Please sign in to save favorites.");
      navigate("/auth");
      return;
    }
    const added = toggleFavoriteDestination(user.id, destination);
    setFavoriteRefreshTick((prev) => prev + 1);
    alert(added ? "Saved to favorites." : "Removed from favorites.");
  };

  return (
    <div>
      {/* Hero */}
      <div className="relative h-[420px] overflow-hidden">
        <img src={heroImg} alt="Travel landscape" className="w-full h-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-r from-background/90 via-background/50 to-transparent" />
        <div className="absolute inset-0 flex items-center">
          <div className="container max-w-6xl mx-auto px-6">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="max-w-lg"
            >
              <h1 className="text-4xl font-bold font-display leading-tight">
                Discover the Beauty of the World
              </h1>
              <p className="text-lg text-muted-foreground mt-3">
                Plan your next journey and uncover unforgettable moments.
              </p>
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleCreateTrip}
                className="mt-6 flex items-center gap-2 rounded-lg bg-primary text-primary-foreground px-6 py-3 font-medium text-sm shadow-lg hover:shadow-xl transition-shadow"
              >
                <Plus className="w-4 h-4" />
                Create New Trip
              </motion.button>
            </motion.div>
          </div>
        </div>
      </div>

      <div className="container max-w-6xl mx-auto px-6 py-10">
        {/* Scenic Highlights */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-display font-semibold">Scenic Highlights</h2>
          <div className="text-sm text-muted-foreground inline-flex items-center gap-1">
            <Sparkles className="w-4 h-4" />
            Explore iconic attractions
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {scenicHighlights.map((spot, i) => (
            <motion.div
              key={spot.id}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              whileHover={{ y: -4 }}
              onClick={() => handleDestinationClick(spot.id)}
              className="rounded-xl bg-card border border-border/50 overflow-hidden shadow-sm hover:shadow-md transition-all cursor-pointer"
            >
              <div className="relative h-44 overflow-hidden">
                <img
                  src={spot.image}
                  alt={spot.name}
                  className="w-full h-full object-cover"
                  onError={(event) => {
                    event.currentTarget.src = FALLBACK_IMAGE;
                  }}
                />
                <button
                  onClick={(event) => {
                    event.stopPropagation();
                    handleToggleFavorite(spot.id);
                  }}
                  className="absolute top-3 right-3 w-9 h-9 rounded-full bg-background/85 backdrop-blur flex items-center justify-center hover:bg-background transition-colors"
                  title="Save to favorites"
                >
                  <Heart
                    className={`w-4 h-4 ${
                      user && user.role === "user" && isFavoriteDestination(user.id, spot.id)
                        ? "text-rose-500 fill-rose-500"
                        : "text-muted-foreground"
                    }`}
                  />
                </button>
              </div>
              <div className="p-4">
                <h3 className="font-display font-semibold">{spot.name}</h3>
                <p className="flex items-center gap-1 mt-1 text-sm text-muted-foreground">
                  <MapPin className="w-3.5 h-3.5" />
                  {spot.location}
                </p>
                <p className="mt-2 text-sm text-muted-foreground">{spot.shortDescription}</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {spot.tags.slice(0, 3).map((tag) => (
                    <span key={tag} className="text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Recommendations */}
        <h2 className="text-2xl font-display font-semibold mt-14 mb-6">Popular Picks</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {popularPicks.map((rec, i) => (
            <motion.div
              key={rec.id}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 + i * 0.1 }}
              whileHover={{ y: -4 }}
              onClick={() => handleDestinationClick(rec.id)}
              className="relative h-64 rounded-xl overflow-hidden shadow-md cursor-pointer group"
            >
              <img
                src={rec.image}
                alt={rec.name}
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                onError={(event) => {
                  event.currentTarget.src = FALLBACK_IMAGE;
                }}
              />
              <button
                onClick={(event) => {
                  event.stopPropagation();
                  handleToggleFavorite(rec.id);
                }}
                className="absolute top-3 right-3 z-10 w-9 h-9 rounded-full bg-background/85 backdrop-blur flex items-center justify-center hover:bg-background transition-colors"
                title="Save to favorites"
              >
                <Heart
                  className={`w-4 h-4 ${
                    user && user.role === "user" && isFavoriteDestination(user.id, rec.id)
                      ? "text-rose-500 fill-rose-500"
                      : "text-muted-foreground"
                  }`}
                />
              </button>
              <div className="absolute inset-0 bg-gradient-to-t from-foreground/70 via-foreground/10 to-transparent" />
              <div className="absolute bottom-5 left-5 right-5">
                <h3 className="text-lg font-display font-semibold text-card">{rec.name}</h3>
                <p className="text-sm text-card/80 mt-1">{rec.shortDescription}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Index;
