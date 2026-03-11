import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useNavigate, useParams } from "react-router-dom";
import { ChevronLeft, MapPin, Calendar, Clock, Star, Users, DollarSign, Info } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import dest1 from "@/assets/destination-1.jpg";
import dest2 from "@/assets/destination-2.jpg";
import dest3 from "@/assets/destination-3.jpg";

interface Attraction {
  name: string;
  category: string;
  description: string;
  best_time: string;
  duration: string;
  price: number;  // 实际价格（人民币）
  crowd_level: string;
}

interface Destination {
  id: string;
  name: string;
  description: string;
  image: string;
  location: string;
  highlights: string[];
  best_season: string;
  recommended_days: number;
  attractions: Attraction[];
}

const destinationsData: Record<string, Destination> = {
  dali: {
    id: "dali",
    name: "Dali, Yunnan",
    description: "Dali is a scenic city in Yunnan province, known for its stunning natural scenery, rich cultural heritage, and unique Bai ethnic traditions. The iconic Erhai Lake and Cangshan Mountains provide a breathtaking backdrop for this ancient town.",
    image: dest1,
    location: "Yunnan Province, China",
    highlights: ["Erhai Lake", "Three Pagodas", "Dali Old Town", "Cangshan Mountain", "Shuanglang Village"],
    best_season: "Spring and Autumn (March-May, September-November)",
    recommended_days: "3-5 days",
    attractions: [
      {
        name: "Erhai Lake",
        category: "Nature",
        description: "A beautiful highland lake known for its crystal-clear waters and scenic views of the Cangshan Mountains.",
        best_time: "Morning or Sunset",
        duration: "2-3 hours",
        price: 0,  // 环湖骑行/漫步免费
        crowd_level: "Medium",
      },
      {
        name: "Dali Old Town",
        category: "Culture",
        description: "An ancient town with over 1,000 years of history, featuring traditional Bai architecture and vibrant local culture.",
        best_time: "Evening",
        duration: "2-4 hours",
        price: 0,  // 古城免费进入
        crowd_level: "High",
      },
      {
        name: "Three Pagodas",
        category: "History",
        description: "Ancient Buddhist pagodas built during the Tang dynasty, representing the pinnacle of Nanzhao architecture.",
        best_time: "Morning",
        duration: "1-2 hours",
        price: 75,  // 成人票
        crowd_level: "Medium",
      },
      {
        name: "Cangshan Mountain",
        category: "Adventure",
        description: "A scenic mountain range with hiking trails offering panoramic views of Erhai Lake.",
        best_time: "Morning",
        duration: "3-5 hours",
        price: 40,  // 苍山索道/门票
        crowd_level: "Low",
      },
    ],
  },
  beijing: {
    id: "beijing",
    name: "Beijing",
    description: "Beijing, the capital of China, is a city where ancient history meets modern development. Home to the Great Wall, the Forbidden City, and countless cultural landmarks, it offers an unparalleled journey through Chinese civilization.",
    image: dest2,
    location: "Beijing Municipality, China",
    highlights: ["Great Wall", "Forbidden City", "Tiananmen Square", "Summer Palace", "Temple of Heaven"],
    best_season: "Spring and Autumn (April-May, September-October)",
    recommended_days: "4-7 days",
    attractions: [
      {
        name: "Great Wall of China",
        category: "History",
        description: "One of the world's most iconic landmarks, stretching over 13,000 miles with breathtaking views.",
        best_time: "Morning",
        duration: "3-5 hours",
        price: 65,  // 成人票（不同段落价格不同）
        crowd_level: "High",
      },
      {
        name: "Forbidden City",
        category: "History",
        description: "The imperial palace complex that served as the home of emperors for over 500 years.",
        best_time: "Morning",
        duration: "2-4 hours",
        price: 60,  // 成人票
        crowd_level: "High",
      },
      {
        name: "Summer Palace",
        category: "Culture",
        description: "A vast imperial garden featuring pavilions, lakes, and beautiful landscaping.",
        best_time: "Afternoon",
        duration: "2-3 hours",
        price: 60,  // 成人票
        crowd_level: "Medium",
      },
      {
        name: "Temple of Heaven",
        category: "Culture",
        description: "A sacred Taoist complex where emperors held annual ceremonies to pray for good harvests.",
        best_time: "Morning",
        duration: "1-2 hours",
        price: 34,  // 成人票
        crowd_level: "Medium",
      },
    ],
  },
  jiuzhaigou: {
    id: "jiuzhaigou",
    name: "Jiuzhaigou Valley",
    description: "Jiuzhaigou is a stunning nature reserve known for its colorful lakes, waterfalls, and snow-capped peaks. This UNESCO World Heritage Site is often described as a fairyland on earth with its crystal-clear waters reflecting vibrant blues and greens.",
    image: dest3,
    location: "Sichuan Province, China",
    highlights: ["Five Flower Lake", "Long Lake", "Pearl Waterfall", "Nuorilang Waterfall", "Rize Valley"],
    best_season: "Autumn (September-November)",
    recommended_days: "2-4 days",
    attractions: [
      {
        name: "Five Flower Lake",
        category: "Nature",
        description: "A spectacular lake known for its vibrant colors and flower-like patterns visible on the lake bed.",
        best_time: "Morning",
        duration: "1-2 hours",
        price: 170,  // 旺季门票
        crowd_level: "High",
      },
      {
        name: "Long Lake",
        category: "Nature",
        description: "The longest and deepest lake in Jiuzhaigou, surrounded by pristine forests and mountains.",
        best_time: "Afternoon",
        duration: "1-2 hours",
        price: 0,  // 已包含在门票中
        crowd_level: "Medium",
      },
      {
        name: "Pearl Waterfall",
        category: "Nature",
        description: "A stunning waterfall where water cascades over marble rocks, creating pearl-like droplets.",
        best_time: "Morning",
        duration: "1 hour",
        price: 0,  // 已包含在门票中
        crowd_level: "Medium",
      },
      {
        name: "Nuorilang Waterfall",
        category: "Nature",
        description: "The largest waterfall in Jiuzhaigou, with a 24-meter drop surrounded by colorful foliage.",
        best_time: "Morning or Afternoon",
        duration: "1-2 hours",
        price: 0,  // 已包含在门票中
        crowd_level: "High",
      },
    ],
  },
};

const DestinationDetail = () => {
  const navigate = useNavigate();
  const { destinationId } = useParams<{ destinationId: string }>();
  const [destination, setDestination] = useState<Destination | null>(null);

  useEffect(() => {
    if (destinationId && destinationsData[destinationId]) {
      setDestination(destinationsData[destinationId]);
    }
  }, [destinationId]);

  const getPriceDisplay = (price: number) => {
    if (price === 0) return "Free";
    return `¥${price}`;
  };

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

              <Button
                onClick={() => navigate("/trip-planner")}
                className="w-full mt-6"
                size="lg"
              >
                Plan a Trip to {destination.name.split(",")[0]}
              </Button>
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
