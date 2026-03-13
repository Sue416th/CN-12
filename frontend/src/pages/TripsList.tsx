import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { ChevronLeft, Calendar, MapPin, Clock, Trash2, Loader2, Eye, CheckCircle2, X, Star } from "lucide-react";
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

type CrowdedLevel = "High" | "Medium" | "Low";
type YesNo = "Yes" | "No";
type TransportLevel = "Excellent" | "Good" | "Fair" | "Poor";

type TripFeedback = {
  overallSatisfaction: number;
  crowdedLevel: CrowdedLevel;
  scheduleReasonable: YesNo;
  transportationConvenience: TransportLevel;
  review: string;
};

type TripEvaluationApiResponse = {
  success: boolean;
  trip_id: string;
  user_id: number;
  trip_title?: string;
  feedback: {
    overall_satisfaction: number;
    crowded_level: string;
    schedule_reasonable: string;
    transportation_convenience: string;
    review: string;
  };
  analysis: {
    sentiment: string;
    score: number;
    suggestion: string;
    satisfaction_score: number;
    issues_detected: string[];
    user_suggestions: string[];
    system_suggestions: string[];
    summary: string;
  };
};

const cityImageModules = import.meta.glob("/src/assets/cities/*.{png,jpg,jpeg,webp}", {
  eager: true,
  import: "default",
}) as Record<string, string>;

const CITY_IMAGE_URLS = Object.fromEntries(
  Object.entries(cityImageModules).map(([path, url]) => {
    const fileName = path.split("/").pop()?.replace(/\.(png|jpg|jpeg|webp)$/i, "");
    return [fileName || path, url];
  }),
) as Record<string, string>;

const getCityAsset = (name: string, fallback: string = "shanghai") =>
  CITY_IMAGE_URLS[name] || CITY_IMAGE_URLS[fallback] || "";

const OFFLINE_FALLBACK_IMAGE = getCityAsset("shanghai");

// 城市地标图片映射 - 使用本地图片
const CITY_IMAGES: Record<string, string> = {
  "shanghai": getCityAsset("shanghai"),
  "上海": getCityAsset("shanghai"),
  "beijing": getCityAsset("beijing"),
  "北京": getCityAsset("beijing"),
  "hangzhou": getCityAsset("hangzhou"),
  "杭州": getCityAsset("hangzhou"),
  "xian": getCityAsset("xian"),
  "xi'an": getCityAsset("xian"),
  "西安": getCityAsset("xian"),
  "chengdu": getCityAsset("chengdu"),
  "成都": getCityAsset("chengdu"),
  "suzhou": getCityAsset("suzhou"),
  "苏州": getCityAsset("suzhou"),
  "dali": getCityAsset("dali"),
  "大理": getCityAsset("dali"),
  "guilin": getCityAsset("guilin"),
  "桂林": getCityAsset("guilin"),
  "lijiang": getCityAsset("lijiang"),
  "丽江": getCityAsset("lijiang"),
  "xiamen": getCityAsset("sanya"),
  "厦门": getCityAsset("sanya"),
  "qingdao": getCityAsset("harbin"),
  "青岛": getCityAsset("harbin"),
  "harbin": getCityAsset("harbin"),
  "哈尔滨": getCityAsset("harbin"),
  "sanya": getCityAsset("sanya"),
  "三亚": getCityAsset("sanya"),
  "lhasa": getCityAsset("lhasa"),
  "拉萨": getCityAsset("lhasa"),
  "huangshan": getCityAsset("emeishan"),
  "黄山": getCityAsset("emeishan"),
  "zhangjiajie": getCityAsset("jiuzhaigou"),
  "张家界": getCityAsset("jiuzhaigou"),
  "jiuzhaigou": getCityAsset("jiuzhaigou"),
  "九寨沟": getCityAsset("jiuzhaigou"),
  "guangzhou": getCityAsset("shanghai"),
  "广州": getCityAsset("shanghai"),
  "shenzhen": getCityAsset("shanghai"),
  "深圳": getCityAsset("shanghai"),
  "hong kong": getCityAsset("shanghai"),
  "香港": getCityAsset("shanghai"),
  "macau": getCityAsset("hangzhou"),
  "澳门": getCityAsset("hangzhou"),
  "ningbo": getCityAsset("hangzhou"),
  "宁波": getCityAsset("hangzhou"),
  "wuzhen": getCityAsset("wuzhen"),
  "乌镇": getCityAsset("wuzhen"),
  "fenghuang": getCityAsset("fenghuang"),
  "凤凰": getCityAsset("fenghuang"),
  "dunhuang": getCityAsset("dunhuang"),
  "敦煌": getCityAsset("dunhuang"),
  "luoyang": getCityAsset("xian"),
  "洛阳": getCityAsset("xian"),
  "taishan": getCityAsset("emeishan"),
  "泰山": getCityAsset("emeishan"),
  "emeishan": getCityAsset("emeishan"),
  "峨眉山": getCityAsset("emeishan"),
};

const getTripImage = (city: string, index: number = 0) => {
  const cityLower = city?.toLowerCase() || "";
  
  // 精确匹配城市名
  if (CITY_IMAGES[cityLower]) {
    return CITY_IMAGES[cityLower];
  }
  
  // 尝试匹配中文城市名
  for (const [key, url] of Object.entries(CITY_IMAGES)) {
    if (cityLower.includes(key)) {
      return url;
    }
  }
  
  // 默认：使用本地离线图，不依赖外网
  return OFFLINE_FALLBACK_IMAGE || CITY_IMAGES["shanghai"] || "";
};

const TripsList = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [trips, setTrips] = useState<Trip[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTrip, setSelectedTrip] = useState<Trip | null>(null);
  const [feedback, setFeedback] = useState<TripFeedback>({
    overallSatisfaction: 0,
    crowdedLevel: "Medium",
    scheduleReasonable: "Yes",
    transportationConvenience: "Good",
    review: "The scenery is beautiful, but the queue was too long and the schedule felt a bit rushed.",
  });
  const [submittingFeedback, setSubmittingFeedback] = useState(false);

  useEffect(() => {
    if (!user || user.role !== "user") {
      navigate("/auth");
      return;
    }
    fetchTrips(user.id);
  }, [user, navigate]);

  const fetchTrips = async (userId: number) => {
    try {
      const response = await axios.get(`/api/trip/list?user_id=${userId}`);
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
      await axios.delete(`/api/trip/delete/${tripId}`);
      setTrips(trips.filter(t => t.id !== tripId));
    } catch (error) {
      console.error("Failed to delete trip:", error);
    }
  };

  const openCompleteModal = (trip: Trip) => {
    setSelectedTrip(trip);
    setFeedback({
      overallSatisfaction: 0,
      crowdedLevel: "Medium",
      scheduleReasonable: "Yes",
      transportationConvenience: "Good",
      review: "The scenery is beautiful, but the queue was too long and the schedule felt a bit rushed.",
    });
  };

  const closeCompleteModal = () => {
    if (!submittingFeedback) {
      setSelectedTrip(null);
    }
  };

  const handleCompleteTrip = async () => {
    if (!selectedTrip) return;
    if (!user) return;
    if (feedback.overallSatisfaction < 1) {
      alert("Please choose an overall satisfaction rating.");
      return;
    }

    setSubmittingFeedback(true);
    try {
      await axios.put(`/api/trip/update/${selectedTrip.id}`, {
        status: "Completed",
      });

      const evaluationResponse = await axios.post<TripEvaluationApiResponse>(
        "/api/trip/evaluate",
        {
          user_id: user.id,
          trip_id: selectedTrip.id,
          overall_satisfaction: feedback.overallSatisfaction,
          crowded_level: feedback.crowdedLevel,
          schedule_reasonable: feedback.scheduleReasonable,
          transportation_convenience: feedback.transportationConvenience,
          review: feedback.review,
        },
      );

      setTrips((prev) =>
        prev.map((trip) => (trip.id === selectedTrip.id ? { ...trip, status: "Completed" } : trip)),
      );

      const payload = evaluationResponse.data;
      setSelectedTrip(null);
      navigate(`/trip-evaluation/${selectedTrip.id}`, {
        state: {
          from: "trips",
          tripTitle: payload.trip_title || selectedTrip.title,
          analysis: payload.analysis,
          feedback: payload.feedback,
        },
      });
    } catch (error) {
      console.error("Failed to complete trip:", error);
      alert("Failed to complete the trip. Please try again.");
    } finally {
      setSubmittingFeedback(false);
    }
  };

  const handleViewEvaluation = async (trip: Trip) => {
    if (!user) return;
    try {
      const response = await axios.get<TripEvaluationApiResponse>(
        `/api/trip/evaluate/${trip.id}?user_id=${user.id}`,
      );
      const payload = response.data;
      navigate(`/trip-evaluation/${trip.id}`, {
        state: {
          from: "trips",
          tripTitle: payload.trip_title || trip.title,
          analysis: payload.analysis,
          feedback: payload.feedback,
        },
      });
    } catch (_error) {
      alert("No evaluation found for this trip yet.");
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
        ) : trips.filter((trip) => String(trip.status).toLowerCase() !== "completed").length === 0 ? (
          <div className="text-center py-20">
            <p className="text-muted-foreground mb-4">No current trips. Completed trips are moved to Travel History.</p>
            <div className="flex items-center justify-center gap-3">
              <Button variant="outline" onClick={() => navigate("/travel-history")}>
                Open Travel History
              </Button>
              <Button onClick={() => navigate("/trip-planner")}>
                Create New Trip
              </Button>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {trips
              .filter((trip) => String(trip.status).toLowerCase() !== "completed")
              .map((trip, index) => (
              <motion.div
                key={trip.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <Card className="hover:shadow-md transition-shadow overflow-hidden">
                  <div className="flex">
                    {/* 城市图片 */}
                    <div className="w-32 h-24 md:w-40 md:h-28 flex-shrink-0 overflow-hidden">
                      <img 
                        src={getTripImage(trip.city, index)} 
                        alt={trip.title}
                        className="w-full h-full object-cover"
                        onError={(event) => {
                          event.currentTarget.src = OFFLINE_FALLBACK_IMAGE;
                        }}
                      />
                    </div>
                    <CardContent className="p-5 flex-1">
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
                          <div className="mt-4 flex items-center gap-2">
                            <Button
                              size="sm"
                              onClick={() =>
                                navigate(`/trip-detail/${trip.id}`, {
                                  state: { from: "trips" },
                                })
                              }
                              className="inline-flex items-center gap-1.5"
                            >
                              <Eye className="w-4 h-4" />
                              View Itinerary
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              disabled={trip.status === "Completed"}
                              onClick={() => openCompleteModal(trip)}
                              className="inline-flex items-center gap-1.5"
                            >
                              <CheckCircle2 className="w-4 h-4" />
                              {trip.status === "Completed" ? "Completed" : "Complete Trip"}
                            </Button>
                            {trip.status === "Completed" && (
                              <Button
                                size="sm"
                                variant="secondary"
                                onClick={() => handleViewEvaluation(trip)}
                              >
                                View Evaluation
                              </Button>
                            )}
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={(e) => {
                            handleDelete(trip.id);
                          }}
                          className="text-muted-foreground hover:text-destructive"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </CardContent>
                  </div>
                </Card>
              </motion.div>
            ))}
          </div>
        )}
      </div>

      {selectedTrip && (
        <div className="fixed inset-0 z-50 bg-black/45 backdrop-blur-[1px] flex items-center justify-center p-4">
          <div className="w-full max-w-2xl rounded-2xl bg-card border border-border shadow-xl">
            <div className="flex items-center justify-between px-6 py-4 border-b border-border/60">
              <div>
                <h2 className="text-xl font-display font-semibold">Trip Feedback</h2>
                <p className="text-sm text-muted-foreground mt-1">{selectedTrip.title}</p>
              </div>
              <button
                onClick={closeCompleteModal}
                className="p-2 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                disabled={submittingFeedback}
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="px-6 py-5 space-y-5">
              <div>
                <p className="text-sm font-medium mb-2">Overall Satisfaction</p>
                <div className="flex items-center gap-2">
                  {[1, 2, 3, 4, 5].map((value) => (
                    <button
                      key={value}
                      onClick={() => setFeedback((prev) => ({ ...prev, overallSatisfaction: value }))}
                      className="p-1"
                    >
                      <Star
                        className={`w-6 h-6 ${
                          value <= feedback.overallSatisfaction
                            ? "text-yellow-500 fill-yellow-500"
                            : "text-muted-foreground"
                        }`}
                      />
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium mb-2">Crowded Level</p>
                  <div className="flex items-center gap-2">
                    {(["High", "Medium", "Low"] as CrowdedLevel[]).map((value) => (
                      <button
                        key={value}
                        onClick={() => setFeedback((prev) => ({ ...prev, crowdedLevel: value }))}
                        className={`px-3 py-1.5 rounded-lg text-sm border ${
                          feedback.crowdedLevel === value
                            ? "border-primary bg-primary/10 text-primary"
                            : "border-border text-muted-foreground"
                        }`}
                      >
                        {value}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <p className="text-sm font-medium mb-2">Schedule Reasonable</p>
                  <div className="flex items-center gap-2">
                    {(["Yes", "No"] as YesNo[]).map((value) => (
                      <button
                        key={value}
                        onClick={() => setFeedback((prev) => ({ ...prev, scheduleReasonable: value }))}
                        className={`px-3 py-1.5 rounded-lg text-sm border ${
                          feedback.scheduleReasonable === value
                            ? "border-primary bg-primary/10 text-primary"
                            : "border-border text-muted-foreground"
                        }`}
                      >
                        {value}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              <div>
                <p className="text-sm font-medium mb-2">Transportation Convenience</p>
                <div className="flex flex-wrap items-center gap-2">
                  {(["Excellent", "Good", "Fair", "Poor"] as TransportLevel[]).map((value) => (
                    <button
                      key={value}
                      onClick={() =>
                        setFeedback((prev) => ({ ...prev, transportationConvenience: value }))
                      }
                      className={`px-3 py-1.5 rounded-lg text-sm border ${
                        feedback.transportationConvenience === value
                          ? "border-primary bg-primary/10 text-primary"
                          : "border-border text-muted-foreground"
                      }`}
                    >
                      {value}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <p className="text-sm font-medium mb-2">Review</p>
                <textarea
                  value={feedback.review}
                  onChange={(event) => setFeedback((prev) => ({ ...prev, review: event.target.value }))}
                  className="w-full min-h-[110px] rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/20"
                  placeholder="The scenery is beautiful, but the queue was too long and the schedule felt a bit rushed."
                />
              </div>
            </div>

            <div className="px-6 py-4 border-t border-border/60 flex items-center justify-end gap-2">
              <Button variant="outline" onClick={closeCompleteModal} disabled={submittingFeedback}>
                Cancel
              </Button>
              <Button onClick={handleCompleteTrip} disabled={submittingFeedback}>
                {submittingFeedback ? "Submitting..." : "Submit and Complete Trip"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TripsList;
