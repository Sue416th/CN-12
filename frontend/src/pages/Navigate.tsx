import { motion } from "framer-motion";
import { Navigation, MapPin, Clock, Route } from "lucide-react";

const itinerary = [
  { time: "09:00", place: "Dali Ancient Town", done: true },
  { time: "11:30", place: "Three Pagodas", done: false },
  { time: "14:00", place: "Erhai Lake Cruise", done: false },
  { time: "17:00", place: "Shuanglang Old Town", done: false },
];

const Navigate = () => {
  return (
    <div className="container max-w-6xl mx-auto px-6 py-8">
      <h1 className="text-2xl font-display font-bold mb-6">Live Navigation</h1>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Map Area */}
        <div className="lg:col-span-2 relative h-[500px] rounded-xl bg-secondary border border-border/50 overflow-hidden flex items-center justify-center">
          <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxjaXJjbGUgY3g9IjIwIiBjeT0iMjAiIHI9IjEiIGZpbGw9IiNjY2MiIG9wYWNpdHk9IjAuMyIvPjwvZz48L3N2Zz4=')] opacity-60" />
          <div className="text-center z-10">
            <Navigation className="w-16 h-16 text-primary mx-auto mb-4" />
            <p className="text-muted-foreground">Loading map...</p>
            <p className="text-sm text-muted-foreground mt-1">Live navigation will be enabled once a map API is connected.</p>
          </div>
          <motion.div
            animate={{ scale: [1, 1.3, 1] }}
            transition={{ repeat: Infinity, duration: 2 }}
            className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-5 h-5 rounded-full bg-primary shadow-lg"
          >
            <div className="absolute inset-0 rounded-full bg-primary/30 animate-ping" />
          </motion.div>
        </div>

        {/* Sidebar */}
        <div className="space-y-5">
          {/* Route Card */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-xl bg-card p-5 shadow-sm border border-border/50"
          >
            <h3 className="font-display font-semibold mb-4">Current Route</h3>
            <div className="flex items-center gap-3 mb-3">
              <div className="w-9 h-9 rounded-full bg-primary/10 flex items-center justify-center">
                <MapPin className="w-4 h-4 text-primary" />
              </div>
              <div>
                <p className="text-sm font-medium">Dali Ancient Town - Renmin Road</p>
                <p className="text-xs text-muted-foreground">Current location</p>
              </div>
            </div>
            <div className="border-l-2 border-dashed border-primary/30 ml-4 pl-6 py-2">
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Route className="w-3 h-3" />
                <span>About a 15-minute walk - 1.2 km</span>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-full bg-accent/10 flex items-center justify-center">
                <MapPin className="w-4 h-4 text-accent" />
              </div>
              <div>
                <p className="text-sm font-medium">Three Pagodas</p>
                <p className="text-xs text-muted-foreground">Next stop</p>
              </div>
            </div>
          </motion.div>

          {/* Itinerary */}
          <div className="rounded-xl bg-card p-5 shadow-sm border border-border/50">
            <h3 className="font-display font-semibold mb-4">Today's Itinerary</h3>
            <div className="space-y-2.5">
              {itinerary.map((item, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.08 }}
                  className={`flex items-center gap-3 p-3 rounded-lg ${
                    item.done ? "bg-primary/5" : "hover:bg-muted/50"
                  } transition-colors`}
                >
                  <div className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${item.done ? "bg-primary" : "bg-border"}`} />
                  <Clock className="w-3.5 h-3.5 text-muted-foreground" />
                  <span className="text-sm text-muted-foreground w-12">{item.time}</span>
                  <span className={`text-sm ${item.done ? "text-muted-foreground line-through" : "font-medium"}`}>{item.place}</span>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Navigate;
