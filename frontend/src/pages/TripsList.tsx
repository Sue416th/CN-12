import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { ChevronLeft, Calendar, MapPin, Clock, Trash2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
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

const TripsList = () => {
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
        setTrips(response.data.trips);
      }
    } catch (error) {
      console.error("Failed to fetch trips:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (tripId: string) => {
    if (!confirm("Are you sure you want to delete this trip?")) return;
    
    try {
      await axios.delete(`http://localhost:3002/api/trip/delete/${tripId}`);
      setTrips(trips.filter(t => t.id !== tripId));
    } catch (error) {
      console.error("Failed to delete trip:", error);
    }
  };

  const statusColors: Record<string, string> = {
    Planning: "bg-secondary text-secondary-foreground",
    Upcoming: "bg-accent text-accent-foreground",
    Ongoing: "bg-primary text-primary-foreground",
    Completed: "bg-muted text-muted-foreground",
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b bg-card/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="container max-w-4xl mx-auto px-6 py-4">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => navigate("/")}>
              <ChevronLeft className="w-5 h-5" />
            </Button>
            <div>
              <h1 className="text-xl font-display font-semibold">My Trips</h1>
              <p className="text-sm text-muted-foreground">View and manage your trips</p>
            </div>
          </div>
        </div>
      </div>

      <div className="container max-w-4xl mx-auto px-6 py-8">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
          </div>
        ) : trips.length === 0 ? (
          <div className="text-center py-20">
            <p className="text-muted-foreground mb-4">No trips yet</p>
            <Button onClick={() => navigate("/trip-planner")}>
              Create Your First Trip
            </Button>
          </div>
        ) : (
          <div className="space-y-4">
            {trips.map((trip, index) => (
              <motion.div
                key={trip.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <Card className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => navigate(`/trip-detail/${trip.id}`)}>
                  <CardContent className="p-5">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="font-display font-semibold text-lg">{trip.title}</h3>
                          <Badge className={statusColors[trip.status] || "bg-muted"}>
                            {trip.status}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-4 text-sm text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <MapPin className="w-4 h-4" />
                            {trip.city.charAt(0).toUpperCase() + trip.city.slice(1)}
                          </span>
                          <span className="flex items-center gap-1">
                            <Calendar className="w-4 h-4" />
                            {trip.days} days
                          </span>
                          {trip.start_date && (
                            <span className="flex items-center gap-1">
                              <Clock className="w-4 h-4" />
                              {trip.start_date}
                            </span>
                          )}
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDelete(trip.id);
                        }}
                        className="text-muted-foreground hover:text-destructive"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default TripsList;
