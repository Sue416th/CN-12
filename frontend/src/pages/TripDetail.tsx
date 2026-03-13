import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { ChevronLeft, Calendar, MapPin, Clock, Thermometer, Cloud, Sun, CloudRain, Wind, Users, AlertCircle, CheckCircle2, Play } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2 } from "lucide-react";
import axios from "axios";

interface TripDetail {
  id: string;
  city: string;
  title: string;
  days: number;
  start_date: string;
  end_date: string;
  status: string;
  profile: {
    interests: string[];
    budget_level: string;
    fitness_level: string;
    group_type: string;
  };
  itinerary: {
    city: string;
    total_days: number;
    days: DayPlan[];
  };
}

interface DayPlan {
  day: number;
  date: string;
  activities: Activity[];
  total_hours: number;
  weather?: WeatherInfo;
}

interface WeatherInfo {
  temp: number;
  condition: string;
  humidity: number;
  wind: number;
}

interface Activity {
  name: string;
  category: string;
  time_needed: number;
  price_level: number;
  tips: string;
  crowd_level?: string;
  open_status?: string;
}

const TripDetail = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { tripId } = useParams<{ tripId: string }>();
  const [trip, setTrip] = useState<TripDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const from = (location.state as { from?: string } | null)?.from;
  const backPath = from === "travel-history" ? "/travel-history" : "/trips";

  useEffect(() => {
    if (tripId) {
      fetchTripDetail(tripId);
    }
  }, [tripId]);

  const fetchTripDetail = async (id: string) => {
    try {
      const response = await axios.get(`http://localhost:3204/api/trip/detail/${id}`);
      if (response.data.success) {
        setTrip(response.data.trip);
      }
    } catch (error) {
      console.error("Failed to fetch trip:", error);
    } finally {
      setLoading(false);
    }
  };

  const getWeatherIcon = (condition: string) => {
    const lower = condition?.toLowerCase() || "";
    if (lower.includes("sun") || lower.includes("clear")) return <Sun className="w-5 h-5 text-yellow-500" />;
    if (lower.includes("rain")) return <CloudRain className="w-5 h-5 text-blue-500" />;
    if (lower.includes("cloud")) return <Cloud className="w-5 h-5 text-gray-400" />;
    return <Thermometer className="w-5 h-5 text-orange-500" />;
  };

  const getCrowdColor = (level?: string) => {
    switch (level) {
      case "low": return "text-green-500";
      case "medium": return "text-yellow-500";
      case "high": return "text-red-500";
      default: return "text-muted-foreground";
    }
  };

  const statusColors: Record<string, string> = {
    Planning: "bg-secondary text-secondary-foreground",
    Upcoming: "bg-accent text-accent-foreground",
    Ongoing: "bg-primary text-primary-foreground",
    Completed: "bg-muted text-muted-foreground",
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!trip) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4">
        <AlertCircle className="w-12 h-12 text-destructive" />
        <p className="text-lg">Trip not found</p>
        <Button onClick={() => navigate(backPath)}>Back</Button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b bg-card/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="container max-w-4xl mx-auto px-6 py-4">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => navigate(backPath)}>
              <ChevronLeft className="w-5 h-5" />
            </Button>
            <div className="flex-1">
              <h1 className="text-xl font-display font-semibold">{trip.title}</h1>
              <p className="text-sm text-muted-foreground">
                {trip.city.charAt(0).toUpperCase() + trip.city.slice(1)} - {trip.days} days
              </p>
            </div>
            <Badge className={statusColors[trip.status] || "bg-muted"}>{trip.status}</Badge>
          </div>
        </div>
      </div>

      <div className="container max-w-4xl mx-auto px-6 py-8">
        {/* Trip Info Card */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-lg">Trip Overview</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Destination</p>
                <p className="font-medium flex items-center gap-2">
                  <MapPin className="w-4 h-4 text-primary" />
                  {trip.city.charAt(0).toUpperCase() + trip.city.slice(1)}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Duration</p>
                <p className="font-medium flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-primary" />
                  {trip.days} days
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Budget</p>
                <p className="font-medium capitalize">{trip.profile?.budget_level || "Medium"}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Group</p>
                <p className="font-medium capitalize flex items-center gap-2">
                  <Users className="w-4 h-4 text-primary" />
                  {trip.profile?.group_type || "Solo"}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Daily Itinerary */}
        <div className="space-y-6">
          {trip.itinerary?.days?.map((day, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <Card>
                <CardHeader className="bg-muted/30">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg flex items-center gap-2">
                      <span className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm">
                        {day.day}
                      </span>
                      Day {day.day}
                    </CardTitle>
                    <div className="flex items-center gap-3">
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <Clock className="w-4 h-4" />
                          {day.total_hours}h
                        </span>
                        {day.weather && (
                          <span className="flex items-center gap-1">
                            {getWeatherIcon(day.weather.condition)}
                            {day.weather.temp}°C
                          </span>
                        )}
                      </div>
                      <Button
                        size="sm"
                        onClick={() =>
                          navigate("/navigate", {
                            state: {
                              day: day.day,
                              date: day.date,
                              activities: day.activities,
                              city: trip.city,
                              tripId: trip.id,
                              tripTitle: trip.title,
                              from: "trip-detail",
                            },
                          })
                        }
                        className="inline-flex items-center gap-1.5"
                      >
                        <Play className="w-4 h-4" />
                        Start
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="pt-4">
                  {/* Weather Info */}
                  {day.weather && (
                    <div className="mb-4 p-3 rounded-lg bg-blue-50 dark:bg-blue-950 flex items-center gap-4">
                      <div className="flex items-center gap-2">
                        {getWeatherIcon(day.weather.condition)}
                        <span className="font-medium">{day.weather.temp}°C</span>
                      </div>
                      <span className="text-sm text-muted-foreground">{day.weather.condition}</span>
                      <span className="text-sm text-muted-foreground">| Humidity: {day.weather.humidity}%</span>
                      <span className="text-sm text-muted-foreground">| Wind: {day.weather.wind} km/h</span>
                    </div>
                  )}

                  {/* Activities */}
                  <div className="space-y-4">
                    {day.activities.map((activity, actIndex) => (
                      <div key={actIndex} className="flex gap-4 p-4 rounded-lg border bg-card hover:shadow-md transition-shadow">
                        <div className="flex flex-col items-center">
                          <div className="w-3 h-3 rounded-full bg-primary" />
                          {actIndex < day.activities.length - 1 && (
                            <div className="w-0.5 h-full bg-border mt-2" />
                          )}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-start justify-between">
                            <div>
                              <h4 className="font-medium">{activity.name}</h4>
                              <p className="text-sm text-muted-foreground capitalize">{activity.category}</p>
                            </div>
                            <div className="text-right">
                              <p className="text-sm font-medium">{activity.time_needed}h</p>
                            </div>
                          </div>

                          {/* Activity Status */}
                          <div className="mt-3 flex items-center gap-4">
                            {activity.open_status && (
                              <span className={`flex items-center gap-1 text-xs ${
                                activity.open_status === "Open" ? "text-green-500" : "text-red-500"
                              }`}>
                                {activity.open_status === "Open" ? (
                                  <CheckCircle2 className="w-3 h-3" />
                                ) : (
                                  <AlertCircle className="w-3 h-3" />
                                )}
                                {activity.open_status}
                              </span>
                            )}
                            {activity.crowd_level && (
                              <span className={`flex items-center gap-1 text-xs ${getCrowdColor(activity.crowd_level)}`}>
                                <Users className="w-3 h-3" />
                                Crowd: {activity.crowd_level}
                              </span>
                            )}
                          </div>

                          {/* Tips */}
                          {activity.tips && (
                            <p className="mt-2 text-sm text-muted-foreground bg-muted/50 p-2 rounded">
                              💡 {activity.tips}
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>

        {/* Travel Tips */}
        <Card className="mt-6">
          <CardHeader>
            <CardTitle className="text-lg">Travel Recommendations</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <p>• Check real-time weather updates before heading out</p>
              <p>• Book popular attractions in advance to avoid crowds</p>
              <p>• Carry appropriate clothing based on weather forecast</p>
              <p>• Start early to make the most of your day</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default TripDetail;
