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

// 城市地标图片映射 - 使用本地图片
const CITY_IMAGES: Record<string, string> = {
  "shanghai": "/src/assets/cities/shanghai.png",
  "上海": "/src/assets/cities/shanghai.png",
  "beijing": "/src/assets/cities/beijing.png",
  "北京": "/src/assets/cities/beijing.png",
  "hangzhou": "/src/assets/cities/hangzhou.png",
  "杭州": "/src/assets/cities/hangzhou.png",
  "xian": "/src/assets/cities/xian.png",
  "xi'an": "/src/assets/cities/xian.png",
  "西安": "/src/assets/cities/xian.png",
  "chengdu": "/src/assets/cities/chengdu.png",
  "成都": "/src/assets/cities/chengdu.png",
  "suzhou": "/src/assets/cities/suzhou.png",
  "苏州": "/src/assets/cities/suzhou.png",
  "dali": "/src/assets/cities/dali.png",
  "大理": "/src/assets/cities/dali.png",
  "guilin": "/src/assets/cities/guilin.png",
  "桂林": "/src/assets/cities/guilin.png",
  "lijiang": "/src/assets/cities/lijiang.png",
  "丽江": "/src/assets/cities/lijiang.png",
  "xiamen": "/src/assets/cities/xiamen.png",
  "厦门": "/src/assets/cities/xiamen.png",
  "qingdao": "/src/assets/cities/qingdao.png",
  "青岛": "/src/assets/cities/qingdao.png",
  "harbin": "/src/assets/cities/harbin.png",
  "哈尔滨": "/src/assets/cities/harbin.png",
  "sanya": "/src/assets/cities/sanya.png",
  "三亚": "/src/assets/cities/sanya.png",
  "lhasa": "/src/assets/cities/lhasa.png",
  "拉萨": "/src/assets/cities/lhasa.png",
  "huangshan": "/src/assets/cities/huangshan.png",
  "黄山": "/src/assets/cities/huangshan.png",
  "zhangjiajie": "/src/assets/cities/zhangjiajie.png",
  "张家界": "/src/assets/cities/zhangjiajie.png",
  "jiuzhaigou": "/src/assets/cities/jiuzhaigou.png",
  "九寨沟": "/src/assets/cities/jiuzhaigou.png",
  "guangzhou": "/src/assets/cities/shenzhen.png",
  "广州": "/src/assets/cities/shenzhen.png",
  "shenzhen": "/src/assets/cities/shenzhen.png",
  "深圳": "/src/assets/cities/shenzhen.png",
  "hong kong": "/src/assets/cities/shanghai.png",
  "香港": "/src/assets/cities/shanghai.png",
  "macau": "/src/assets/cities/hangzhou.png",
  "澳门": "/src/assets/cities/hangzhou.png",
  "ningbo": "/src/assets/cities/hangzhou.png",
  "宁波": "/src/assets/cities/hangzhou.png",
  "wuzhen": "/src/assets/cities/wuzhen.png",
  "乌镇": "/src/assets/cities/wuzhen.png",
  "fenghuang": "/src/assets/cities/fenghuang.png",
  "凤凰": "/src/assets/cities/fenghuang.png",
  "dunhuang": "/src/assets/cities/dunhuang.png",
  "敦煌": "/src/assets/cities/dunhuang.png",
  "luoyang": "/src/assets/cities/luoyang.png",
  "洛阳": "/src/assets/cities/luoyang.png",
  "taishan": "/src/assets/cities/taishan.png",
  "泰山": "/src/assets/cities/taishan.png",
  "emeishan": "/src/assets/cities/emeishan.png",
  "峨眉山": "/src/assets/cities/emeishan.png",
};

const defaultImages = [
  "/src/assets/destination-1.jpg",
  "/src/assets/destination-2.jpg",
  "/src/assets/destination-3.jpg",
];

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
  
  // 默认 - 根据索引循环使用默认图片
  return defaultImages[index % 3];
};

const TripsList = () => {
  const navigate = useNavigate();
  const [trips, setTrips] = useState<Trip[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTrips();
  }, []);

  const fetchTrips = async () => {
    try {
      const response = await axios.get("http://localhost:3004/api/trip/list?user_id=1");
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
      await axios.delete(`http://localhost:3004/api/trip/delete/${tripId}`);
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
                <Card className="hover:shadow-md transition-shadow cursor-pointer overflow-hidden" onClick={() => navigate(`/trip-detail/${trip.id}`)}>
                  <div className="flex">
                    {/* 城市图片 */}
                    <div className="w-32 h-24 md:w-40 md:h-28 flex-shrink-0 overflow-hidden">
                      <img 
                        src={getTripImage(trip.city, index)} 
                        alt={trip.title}
                        className="w-full h-full object-cover"
                      />
                    </div>
                    <CardContent className="p-5 flex-1 flex flex-col justify-center">
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
                  </div>
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
