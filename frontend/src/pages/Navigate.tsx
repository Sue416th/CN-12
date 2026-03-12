import { motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import { Navigation, MapPin, Clock, Route, Search, Play, Pause, X } from "lucide-react";

const itinerary = [
  { time: "09:00", place: "Dali Ancient Town", done: true },
  { time: "11:30", place: "Three Pagodas", done: false },
  { time: "14:00", place: "Erhai Lake Cruise", done: false },
  { time: "17:00", place: "Shuanglang Old Town", done: false },
];

const Navigate = () => {
  const mapRef = useRef<HTMLDivElement>(null);
  const routeLineRef = useRef<any>(null);
  const [map, setMap] = useState<any>(null);
  const [currentMarker, setCurrentMarker] = useState<any>(null);
  const [initialMarker, setInitialMarker] = useState<any>(null);
  const [watchId, setWatchId] = useState<any>(null);
  const [navigationMode, setNavigationMode] = useState(false);
  const [currentRoute, setCurrentRoute] = useState<any>(null);
  const [lastKnownPosition, setLastKnownPosition] = useState<any>(null);
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [mode, setMode] = useState("walking");
  const [loading, setLoading] = useState(false);
  const [routeInfo, setRouteInfo] = useState<any>(null);
  const [currentLocation, setCurrentLocation] = useState<any>(null);
  const [lastRouteUpdate, setLastRouteUpdate] = useState<number>(0);

  // 初始化地图
  useEffect(() => {
    // 直接使用index.html中已经加载的高德地图API
    if (mapRef.current && typeof window !== 'undefined' && window.AMap) {
      try {
        const amap = new window.AMap.Map(mapRef.current, {
          zoom: 12,
          center: [100.199716, 25.680272] // 大理古城坐标
        });

        // 添加控件
        window.AMap.plugin(['AMap.Scale', 'AMap.ToolBar', 'AMap.MapType'], function() {
          amap.addControl(new window.AMap.Scale());
          amap.addControl(new window.AMap.ToolBar());
          amap.addControl(new window.AMap.MapType());
        });

        setMap(amap);

        // 获取当前位置
        getCurrentLocation(amap);
      } catch (error) {
        // 静默处理错误
      }
    }
  }, []);

  // 获取当前位置
  const getCurrentLocation = (amap: any) => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          const location = [longitude, latitude];
          
          // 移动地图到当前位置
          amap.setCenter(location);
          
          // 添加初始定位标记
          if (initialMarker) {
            amap.remove(initialMarker);
          }
          
          const marker = new window.AMap.Marker({
            position: location,
            icon: new window.AMap.Icon({
              size: new window.AMap.Size(25, 25),
              image: 'https://a.amap.com/jsapi_demos/static/demo-center/icons/poi-marker-red.png',
              imageSize: new window.AMap.Size(25, 25)
            })
          });
          
          marker.setMap(amap);
          setInitialMarker(marker);
          setCurrentLocation(location);
          setLastKnownPosition(location);
          
          // 不再自动设置起点为当前位置
        },
        (error) => {
          // 静默处理错误
        }
      );
    }
  };

  // 获取导航路线
  const getRoute = async () => {
    if (!start || !end) {
      alert('Please enter start and end points');
      return;
    }

    setLoading(true);

    try {
      // 调用后端导航API
      const encodedStart = encodeURIComponent(start);
      const encodedEnd = encodeURIComponent(end);
      const response = await fetch(`http://localhost:8000/cgi-bin/navigation.py?start=${encodedStart}&end=${encodedEnd}&mode=${mode}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      const data = await response.json();

      if (data.status === 'success') {
        const route = data.route;
        setRouteInfo(route);
        setCurrentRoute(route);

        // 清除之前的路线
        if (routeLineRef.current) {
          map.remove(routeLineRef.current);
          routeLineRef.current = null; // 确保路线引用被清除
        }

        // 绘制路线
        if (route.path && route.path.length > 0) {
          const line = new window.AMap.Polyline({
            path: route.path,
            strokeColor: '#3366FF',
            strokeWeight: 4,
            strokeOpacity: 0.8
          });

          line.setMap(map);
          routeLineRef.current = line;

          // 调整地图视野
          map.setFitView([line]);
        }
      } else {
        alert('Route planning failed');
      }
    } catch (error) {
      alert('Failed to get route, please check network connection');
    } finally {
      setLoading(false);
    }
  };

  // 开始实时导航
  const startNavigation = () => {
    if (!currentRoute || !end) {
      alert('Please plan route first');
      return;
    }

    setNavigationMode(true);

    // 开始监听位置变化
    if (navigator.geolocation) {
      const id = navigator.geolocation.watchPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          const location = [longitude, latitude];
          
          setLastKnownPosition(location);

          // 更新当前位置标记
          if (currentMarker) {
            map.remove(currentMarker);
          }

          const marker = new window.AMap.Marker({
            position: location,
            icon: new window.AMap.Icon({
              size: new window.AMap.Size(25, 25),
              image: 'https://a.amap.com/jsapi_demos/static/demo-center/icons/poi-marker-blue.png',
              imageSize: new window.AMap.Size(25, 25)
            })
          });

          marker.setMap(map);
          setCurrentMarker(marker);

          // 实时重新规划路线（从当前位置到终点）- 添加防抖机制
          const now = Date.now();
          if (now - lastRouteUpdate > 2000) { // 每2秒更新一次路线
            const start = `${longitude},${latitude}`;
            const url = `http://localhost:8000/cgi-bin/navigation.py?start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}&mode=${encodeURIComponent(mode)}`;
            
            fetch(url)
            .then(response => response.json())
            .then(data => {
              if (data.status === 'success') {
                const route = data.route;
                setRouteInfo(route);
                setCurrentRoute(route);
                setLastRouteUpdate(now);

                // 清除之前的路线
                if (routeLineRef.current) {
                  map.remove(routeLineRef.current);
                  routeLineRef.current = null; // 确保路线引用被清除
                }

                // 绘制新路线
                if (route.path && route.path.length > 0) {
                  const line = new window.AMap.Polyline({
                    path: route.path,
                    strokeColor: '#3366FF',
                    strokeWeight: 4,
                    strokeOpacity: 0.8
                  });

                  line.setMap(map);
                  routeLineRef.current = line;

                  // 调整地图视野
                  map.setFitView([line, marker]);
                }
              }
            })
            .catch(error => {
              // 静默处理错误
            });
          }

          // 可选：更新地图中心
          // map.setCenter(location);
        },
        (error) => {
          // 静默处理错误
        },
        {
          enableHighAccuracy: true,
          timeout: 5000,
          maximumAge: 0
        }
      );

      setWatchId(id);
    }
  };

  // 停止实时导航
  const stopNavigation = () => {
    setNavigationMode(false);

    if (watchId) {
      navigator.geolocation.clearWatch(watchId);
      setWatchId(null);
    }

    if (currentMarker) {
      map.remove(currentMarker);
      setCurrentMarker(null);
    }
  };

  return (
    <div className="container max-w-6xl mx-auto px-6 py-8">
      <h1 className="text-2xl font-display font-bold mb-6">Live Navigation</h1>
      
      {/* 导航控制 */}
      <div className="mb-6 p-4 bg-secondary rounded-xl border border-border/50">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Start:</label>
            <div className="relative">
              <input
                type="text"
                value={start}
                onChange={(e) => setStart(e.target.value)}
                placeholder="Please enter start address"
                className="w-full px-3 py-2 border border-border rounded-lg pr-10"
              />
              <button
                onClick={() => start && setStart('')}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground"
              >
                {start && <Search className="w-4 h-4" />}
              </button>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">End:</label>
            <div className="relative">
              <input
                type="text"
                value={end}
                onChange={(e) => setEnd(e.target.value)}
                placeholder="Please enter end address"
                className="w-full px-3 py-2 border border-border rounded-lg pr-10"
              />
              <button
                onClick={() => end && setEnd('')}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground"
              >
                {end && <Search className="w-4 h-4" />}
              </button>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Transportation:</label>
            <select
              value={mode}
              onChange={(e) => setMode(e.target.value)}
              className="w-full px-3 py-2 border border-border rounded-lg"
            >
              <option value="driving">Driving</option>
              <option value="walking">Walking</option>
            </select>
          </div>
          <div className="flex items-end">
            <button
              onClick={getRoute}
              disabled={loading}
              className="w-full px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Calculating...' : 'Plan Route'}
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Map Area */}
        <div className="lg:col-span-2 relative h-[500px] rounded-xl bg-secondary border border-border/50 overflow-hidden">
          <div ref={mapRef} className="w-full h-full" />
          {!map && (
            <div className="absolute inset-0 flex items-center justify-center z-10">
              <div className="text-center">
                <Navigation className="w-16 h-16 text-primary mx-auto mb-4" />
                <p className="text-muted-foreground">Loading map...</p>
                <p className="text-sm text-muted-foreground mt-1">Map is loading, please wait...</p>
              </div>
            </div>
          )}
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
            {routeInfo ? (
              <>
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-9 h-9 rounded-full bg-primary/10 flex items-center justify-center">
                    <MapPin className="w-4 h-4 text-primary" />
                  </div>
                  <div>
                    <p className="text-sm font-medium">{start}</p>
                    <p className="text-xs text-muted-foreground">Start</p>
                  </div>
                </div>
                <div className="border-l-2 border-dashed border-primary/30 ml-4 pl-6 py-2">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <Route className="w-3 h-3" />
                    <span>{routeInfo.time} - {routeInfo.distance}</span>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-full bg-accent/10 flex items-center justify-center">
                    <MapPin className="w-4 h-4 text-accent" />
                  </div>
                  <div>
                    <p className="text-sm font-medium">{end}</p>
                    <p className="text-xs text-muted-foreground">End</p>
                  </div>
                </div>
                
                {/* Navigation Control Buttons */}
                <div className="mt-4 flex gap-2">
                  {!navigationMode ? (
                    <button
                      onClick={startNavigation}
                      className="flex-1 px-3 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors flex items-center justify-center gap-1"
                    >
                      <Play className="w-4 h-4" />
                      <span>Start Navigation</span>
                    </button>
                  ) : (
                    <button
                      onClick={stopNavigation}
                      className="flex-1 px-3 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors flex items-center justify-center gap-1"
                    >
                      <X className="w-4 h-4" />
                      <span>Stop Navigation</span>
                    </button>
                  )}
                </div>
              </>
            ) : (
              <div className="text-center py-4 text-muted-foreground">
                <p>Please enter start and end points, click Plan Route</p>
              </div>
            )}
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

          {/* 导航步骤 */}
          {routeInfo && routeInfo.steps && routeInfo.steps.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              className="rounded-xl bg-card p-5 shadow-sm border border-border/50"
            >
              <h3 className="font-display font-semibold mb-4">Navigation Steps</h3>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {routeInfo.steps.map((step: string, index: number) => (
                  <div key={index} className="text-sm p-2 hover:bg-muted/50 rounded-lg">
                    {index + 1}. {step}
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Navigate;
