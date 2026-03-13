import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { ChevronLeft, Calendar, MapPin, Clock, Eye } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import axios from "axios";
import { useAuth } from "@/context/AuthContext";

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

const TravelHistory = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [trips, setTrips] = useState<Trip[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHistory = async () => {
      if (!user || user.role !== "user") {
        navigate("/auth");
        return;
      }
      try {
        const response = await axios.get(`/api/trip/list?user_id=${user.id}`);
        if (response.data.success) {
          const allTrips: Trip[] = response.data.trips || [];
          const completed = allTrips.filter((trip) => String(trip.status).toLowerCase() === "completed");
          setTrips(completed);
        }
      } catch (error) {
        console.error("Failed to fetch travel history:", error);
      } finally {
        setLoading(false);
      }
    };

    void fetchHistory();
  }, [user, navigate]);

  return (
    <div className="min-h-screen bg-background">
      <div className="border-b bg-card/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="container max-w-4xl mx-auto px-6 py-4">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => navigate("/profile")}>
              <ChevronLeft className="w-5 h-5" />
            </Button>
            <div>
              <h1 className="text-xl font-display font-semibold">Travel History</h1>
              <p className="text-sm text-muted-foreground">Your completed trips</p>
            </div>
          </div>
        </div>
      </div>

      <div className="container max-w-4xl mx-auto px-6 py-8">
        {loading ? (
          <div className="text-sm text-muted-foreground">Loading travel history...</div>
        ) : trips.length === 0 ? (
          <div className="text-center py-16 rounded-xl border border-border/60 bg-card">
            <p className="text-muted-foreground mb-3">No completed trips yet.</p>
            <Button onClick={() => navigate("/trips")}>Go to Current Trips</Button>
          </div>
        ) : (
          <div className="space-y-4">
            {trips.map((trip, index) => (
              <motion.div
                key={trip.id}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <Card className="border border-border/60">
                  <CardContent className="p-5">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="font-display font-semibold text-lg">{trip.title}</h3>
                          <Badge className="bg-emerald-100 text-emerald-700 border border-emerald-200">
                            Completed
                          </Badge>
                        </div>
                        <div className="flex items-center gap-4 text-sm text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <MapPin className="w-4 h-4" />
                            {trip.city}
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
                      <div className="flex items-center gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() =>
                            navigate(`/trip-detail/${trip.id}`, {
                              state: { from: "travel-history" },
                            })
                          }
                          className="inline-flex items-center gap-1.5"
                        >
                          <Eye className="w-4 h-4" />
                          View Itinerary
                        </Button>
                        <Button
                          size="sm"
                          onClick={() =>
                            navigate(`/trip-evaluation/${trip.id}`, {
                              state: { from: "travel-history" },
                            })
                          }
                        >
                          View Evaluation
                        </Button>
                      </div>
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

export default TravelHistory;

