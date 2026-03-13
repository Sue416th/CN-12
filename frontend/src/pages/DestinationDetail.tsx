import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useNavigate, useParams } from "react-router-dom";
import { ChevronLeft, MapPin, Calendar, Clock, Star, Users, Info, Heart } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import fallbackImage from "@/assets/destination-2.jpg";
import { getDestinationById, type Destination } from "@/lib/destinations";
import { isFavoriteDestination, toggleFavoriteDestination } from "@/lib/favorites";
import { useAuth } from "@/context/AuthContext";

const FALLBACK_IMAGE = fallbackImage;

const DestinationDetail = () => {
  const navigate = useNavigate();
  const { destinationId } = useParams<{ destinationId: string }>();
  const { isLoggedIn, user } = useAuth();
  const [destination, setDestination] = useState<Destination | null>(null);
  const [favoriteVersion, setFavoriteVersion] = useState(0);

  useEffect(() => {
    setDestination(getDestinationById(destinationId));
  }, [destinationId]);

  const getPriceDisplay = (price: number) => {
    if (price === 0) return "Free";
    return `¥${price}`;
  };

  const handleToggleFavorite = () => {
    if (!destination) return;
    if (!isLoggedIn || !user || user.role !== "user") {
      alert("Please sign in to save favorites.");
      navigate("/auth");
      return;
    }
    const added = toggleFavoriteDestination(user.id, destination);
    setFavoriteVersion((prev) => prev + 1);
    alert(added ? "Saved to favorites." : "Removed from favorites.");
  };

  const isFavorite =
    !!destination &&
    !!user &&
    user.role === "user" &&
    isFavoriteDestination(user.id, destination.id) &&
    favoriteVersion >= 0;

  const getCategoryColor = (category: string) => {
    switch (category.toLowerCase()) {
      case "nature":
        return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100";
      case "history":
        return "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-100";
      case "culture":
        return "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-100";
      case "adventure":
        return "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-100";
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-100";
    }
  };

  if (!destination) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4">
        <Info className="w-12 h-12 text-muted-foreground" />
        <p className="text-lg text-muted-foreground">Destination not found</p>
        <Button onClick={() => navigate("/")}>Back to Home</Button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header Image */}
      <div className="relative h-[350px] overflow-hidden">
        <img
          src={destination.image}
          alt={destination.name}
          className="w-full h-full object-cover"
          onError={(event) => {
            event.currentTarget.src = FALLBACK_IMAGE;
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-t from-background via-background/30 to-transparent" />
        <div className="absolute top-4 left-4">
          <Button variant="ghost" size="icon" onClick={() => navigate("/")} className="bg-background/80 backdrop-blur-sm">
            <ChevronLeft className="w-5 h-5" />
          </Button>
        </div>
      </div>

      <div className="container max-w-4xl mx-auto px-6 -mt-20 relative z-10">
        {/* Destination Info */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <Card className="mb-6">
            <CardHeader>
              <div className="flex items-center gap-2 text-muted-foreground mb-2">
                <MapPin className="w-4 h-4" />
                <span className="text-sm">{destination.location}</span>
              </div>
              <CardTitle className="text-3xl">{destination.name}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground leading-relaxed">{destination.description}</p>

              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mt-6">
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-primary" />
                  <div>
                    <p className="text-xs text-muted-foreground">Best Season</p>
                    <p className="text-sm font-medium">{destination.best_season}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-primary" />
                  <div>
                    <p className="text-xs text-muted-foreground">Recommended</p>
                    <p className="text-sm font-medium">{destination.recommended_days}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Star className="w-4 h-4 text-primary" />
                  <div>
                    <p className="text-xs text-muted-foreground">Top Pick</p>
                    <p className="text-sm font-medium">Must Visit</p>
                  </div>
                </div>
              </div>

              <div className="mt-6">
                <p className="text-sm font-medium mb-2">Highlights</p>
                <div className="flex flex-wrap gap-2">
                  {destination.highlights.map((highlight, index) => (
                    <Badge key={index} variant="outline" className="bg-primary/10">
                      {highlight}
                    </Badge>
                  ))}
                </div>
              </div>

              <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-3">
                <Button
                  onClick={() => navigate("/trip-planner")}
                  className="w-full"
                  size="lg"
                >
                  Plan a Trip to {destination.name}
                </Button>
                <Button
                  variant={isFavorite ? "secondary" : "outline"}
                  onClick={handleToggleFavorite}
                  className="w-full inline-flex items-center gap-2"
                  size="lg"
                >
                  <Heart className={`w-4 h-4 ${isFavorite ? "fill-current" : ""}`} />
                  {isFavorite ? "Saved" : "Save to Favorites"}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Attractions */}
          <div className="mb-8">
            <h2 className="text-2xl font-display font-semibold mb-4">Top Attractions</h2>
            <div className="space-y-4">
              {destination.attractions.map((attraction, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <Card className="hover:shadow-md transition-shadow">
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between">
                        <div>
                          <CardTitle className="text-lg">{attraction.name}</CardTitle>
                          <div className="flex items-center gap-2 mt-1">
                            <Badge className={getCategoryColor(attraction.category)}>
                              {attraction.category}
                            </Badge>
                            <span className="text-xs text-muted-foreground flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {attraction.duration}
                            </span>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-medium">{getPriceDisplay(attraction.price)}</p>
                          <p className="text-xs text-muted-foreground flex items-center gap-1 justify-end">
                            <Users className="w-3 h-3" />
                            {attraction.crowd_level} crowd
                          </p>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-muted-foreground">{attraction.description}</p>
                      <div className="mt-3 flex items-center gap-2 text-xs text-muted-foreground">
                        <Info className="w-3 h-3" />
                        <span>Best time to visit: {attraction.best_time}</span>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default DestinationDetail;
