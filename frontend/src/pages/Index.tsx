import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { Plus, Calendar, MapPin, ChevronRight, Loader2 } from "lucide-react";
import heroImg from "@/assets/hero-travel.jpg";
import dest1 from "@/assets/destination-1.jpg";
import dest2 from "@/assets/destination-2.jpg";
import dest3 from "@/assets/destination-3.jpg";
import axios from "axios";

interface Trip {
  id: string;
  city: string;
  title: string;
  days: number;
  start_date: string;
  end_date: string;
  status: string;
  created_at: string;
}

const statusColors: Record<string, string> = {
  Ongoing: "bg-primary text-primary-foreground",
  Upcoming: "bg-accent text-accent-foreground",
  Planning: "bg-secondary text-secondary-foreground",
  Completed: "bg-muted text-muted-foreground",
};

const recommendations = [
  { id: "dali", image: dest1, title: "Dali, Yunnan", desc: "Ancient charm of the old town and scenic Erhai Lake." },
  { id: "beijing", image: dest2, title: "Beijing", desc: "Experience the grandeur of the Great Wall and imperial palaces." },
  { id: "jiuzhaigou", image: dest3, title: "Jiuzhaigou", desc: "A dreamlike landscape painted with crystal waters and color." },
];

const Index = () => {
  const navigate = useNavigate();
  const [trips, setTrips] = useState<Trip[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTrips();
  }, []);

  const fetchTrips = async () => {
    try {
      const response = await axios.get("http://localhost:3002/api/trip/list?user_id=1");
      if (response.data.success) {
        setTrips(response.data.trips || []);
      }
    } catch (error) {
      console.error("Failed to fetch trips:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTrip = () => {
    navigate("/trip-planner");
  };

  const handleViewAll = () => {
    navigate("/trips");
  };

  const handleTripClick = (tripId: string) => {
    navigate(`/trip-detail/${tripId}`);
  };

  const handleDestinationClick = (destinationId: string) => {
    navigate(`/destination/${destinationId}`);
  };

  const getTripImage = (city: string, index: number = 0) => {
    const cityLower = city?.toLowerCase() || "";
    if (cityLower.includes("dali") || cityLower.includes("yunnan")) return dest1;
    if (cityLower.includes("beijing") || cityLower.includes("wall")) return dest2;
    if (cityLower.includes("jiuzhaigou")) return dest3;
    if (cityLower.includes("hangzhou") || cityLower.includes("west lake")) return dest1;
    if (cityLower.includes("shanghai")) return dest2;
    if (cityLower.includes("chengdu")) return dest3;
    if (cityLower.includes("guangzhou")) return dest1;
    if (cityLower.includes("xian") || cityLower.includes("xi'an")) return dest2;
    // Default - cycle through images based on index
    const images = [dest1, dest2, dest3];
    return images[index % 3];
  };

  const formatDate = (dateStr: string) => {
    if (!dateStr) return "TBD";
    try {
      const date = new Date(dateStr);
      return `Departs ${date.toLocaleDateString("en-US", { month: "short", day: "numeric" })}`;
    } catch {
      return dateStr;
    }
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
        {/* Trips */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-display font-semibold">My Trips</h2>
          <button onClick={handleViewAll} className="text-sm text-muted-foreground hover:text-foreground flex items-center gap-1 transition-colors">
            View All <ChevronRight className="w-4 h-4" />
          </button>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
          </div>
        ) : trips.length === 0 ? (
          <div className="text-center py-12 bg-muted/30 rounded-xl">
            <p className="text-muted-foreground mb-4">No trips yet. Create your first adventure!</p>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleCreateTrip}
              className="flex items-center gap-2 rounded-lg bg-primary text-primary-foreground px-6 py-3 font-medium text-sm shadow-lg hover:shadow-xl transition-shadow mx-auto"
            >
              <Plus className="w-4 h-4" />
              Create New Trip
            </motion.button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {trips.slice(0, 3).map((trip, i) => (
              <motion.div
                key={trip.id}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                whileHover={{ y: -4 }}
                onClick={() => handleTripClick(trip.id)}
                className="rounded-xl bg-card border border-border/50 overflow-hidden shadow-sm hover:shadow-md transition-all cursor-pointer group"
              >
                <div className="relative h-44 overflow-hidden">
                  <img
                    src={getTripImage(trip.city, i)}
                    alt={trip.title}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                  />
                  <span className={`absolute top-3 right-3 text-xs px-3 py-1 rounded-full ${statusColors[trip.status] || "bg-muted"}`}>
                    {trip.status}
                  </span>
                </div>
                <div className="p-4">
                  <h3 className="font-display font-semibold">{trip.title}</h3>
                  <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                    <span className="flex items-center gap-1"><Calendar className="w-3.5 h-3.5" />{trip.days} days</span>
                    <span className="flex items-center gap-1"><MapPin className="w-3.5 h-3.5" />{formatDate(trip.start_date)}</span>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}

        {/* Recommendations */}
        <h2 className="text-2xl font-display font-semibold mt-14 mb-6">Popular Picks</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {recommendations.map((rec, i) => (
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
                alt={rec.title}
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-foreground/70 via-foreground/10 to-transparent" />
              <div className="absolute bottom-5 left-5 right-5">
                <h3 className="text-lg font-display font-semibold text-card">{rec.title}</h3>
                <p className="text-sm text-card/80 mt-1">{rec.desc}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Index;
