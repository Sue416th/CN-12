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
      const response = await axios.get("/api/trip/list?user_id=1");
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
