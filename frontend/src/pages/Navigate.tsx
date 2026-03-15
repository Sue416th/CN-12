import { motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import { Navigation, MapPin, Clock, Route, Search, Play, Pause, X, Calendar, MapPin as MapPinIcon, Footprints, Car } from "lucide-react";

const Navigate = () => {
  const location = useLocation();
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
  const [itineraryRoutes, setItineraryRoutes] = useState<any>({});
  const [currentItineraryIndex, setCurrentItineraryIndex] = useState<number>(0);
  
  // 从状态中获取行程数据
  const { day, date, activities, city } = location.state || {};
  
  // 生成当天的行程安排
  const itinerary = activities ? activities.map((activity: any, index: number) => {
    // 简单计算时间，假设从9点开始
    const startHour = 9 + Math.floor(index * 2.5);
    const startMinute = (index * 30) % 60;
    const time = `${startHour.toString().padStart(2, '0')}:${startMinute.toString().padStart(2, '0')}`;
    return {
      time,
      place: activity.name,
      done: index === 0, // 第一个景点默认为已完成
      category: activity.category
    };
  }) : [
    { time: "09:00", place: "Dali Ancient Town", done: true, category: "Historical" },
    { time: "11:30", place: "Three Pagodas", done: false, category: "Cultural" },
    { time: "14:00", place: "Erhai Lake Cruise", done: false, category: "Natural" },
    { time: "17:00", place: "Shuanglang Old Town", done: false, category: "Historical" },
  ];

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

  // 获取行程路线信息
  useEffect(() => {
    getItineraryRoutes();
  }, [itinerary.length]);

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
      console.error('Navigation API error:', error);
      if (error instanceof Error) {
        alert(`Failed to get route: ${error.message}`);
      } else {
        alert('Failed to get route, please check network connection');
      }
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
          if (now - lastRouteUpdate > 5000) { // 每5秒更新一次路线
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
          enableHighAccuracy: false, // 关闭高精度定位，减少位置跳变
          timeout: 10000, // 增加超时时间
          maximumAge: 30000 // 允许使用30秒内的缓存位置
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

  // 获取行程路线信息
  const getItineraryRoutes = async () => {
    if (itinerary.length < 2) return;

    const routes: any = {};
    
    for (let i = 0; i < itinerary.length - 1; i++) {
      const startPlace = itinerary[i].place;
      const endPlace = itinerary[i + 1].place;
      
      // 获取步行路线
      try {
        const encodedStart = encodeURIComponent(startPlace);
        const encodedEnd = encodeURIComponent(endPlace);
        const encodedCity = encodeURIComponent(city || '杭州');
        const response = await fetch(`http://localhost:8000/cgi-bin/navigation.py?start=${encodedStart}&end=${encodedEnd}&mode=walking&city=${encodedCity}`);
        const data = await response.json();
        
        if (data.status === 'success') {
          routes[`${i}-${i+1}-walking`] = data.route;
        }
      } catch (error) {
        console.error('Error getting walking route:', error);
      }
      
      // 获取驾车路线
      try {
        const encodedStart = encodeURIComponent(startPlace);
        const encodedEnd = encodeURIComponent(endPlace);
        const encodedCity = encodeURIComponent(city || '杭州');
        const response = await fetch(`http://localhost:8000/cgi-bin/navigation.py?start=${encodedStart}&end=${encodedEnd}&mode=driving&city=${encodedCity}`);
        const data = await response.json();
        
        if (data.status === 'success') {
          routes[`${i}-${i+1}-driving`] = data.route;
        }
      } catch (error) {
        console.error('Error getting driving route:', error);
      }
    }
    
    setItineraryRoutes(routes);
  };

  // 启动行程导航
  const startItineraryNavigation = () => {
    if (itinerary.length < 2) return;
    
    // 停止当前可能的导航
    stopNavigation();
    
    // 重置行程索引
    setCurrentItineraryIndex(0);
    
    // 开始第一个导航段
    startNavigationSegment(0);
  };

  // 启动单个导航段
  const startNavigationSegment = (index: number) => {
    if (index >= itinerary.length - 1) {
      // 行程结束
      stopNavigation();
      return;
    }
    
    const startPlace = itinerary[index].place;
    const endPlace = itinerary[index + 1].place;
    
    // 复用现有的实时导航逻辑
    // 设置起点和终点
    setStart(startPlace);
    setEnd(endPlace);
    setMode('walking'); // 默认步行
    
    // 启动实时导航
    startNavigation();
    
    // 监听导航完成
    // 这里可以添加逻辑来检测是否到达目的地
    // 简单实现：设置一个定时器，根据路线时间自动切换到下一段
    const routeKey = `${index}-${index+1}-walking`;
    if (itineraryRoutes[routeKey]) {
      const durationStr = itineraryRoutes[routeKey].time;
      // 简单解析时间（分钟）
      const minutes = parseInt(durationStr.match(/\d+/)?.[0] || '0');
      if (minutes > 0) {
        setTimeout(() => {
          // 标记当前景点为已完成
          const updatedItinerary = [...itinerary];
          updatedItinerary[index].done = true;
          setItinerary(updatedItinerary);
          
          // 切换到下一段
          setCurrentItineraryIndex(index + 1);
          startNavigationSegment(index + 1);
        }, minutes * 60 * 1000); // 转换为毫秒
      }
    }
  };

  return (
    <div className="container max-w-6xl mx-auto px-6 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-display font-bold">Live Navigation</h1>
        {city && date && (
          <div className="mt-2 flex items-center gap-4 text-muted-foreground">
            <div className="flex items-center gap-1">
              <MapPinIcon className="w-4 h-4" />
              <span>{city}</span>
            </div>
            <div className="flex items-center gap-1">
              <Calendar className="w-4 h-4" />
              <span>Day {day} - {date}</span>
            </div>
          </div>
        )}
      </div>
      
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
            {itinerary.length > 0 ? (
              <>
                {itinerary.map((item, i) => (
                  <>
                    {i > 0 && (
                      <div className="border-l-2 border-dashed border-primary/30 ml-4 pl-6 py-2">
                        <div className="flex flex-col gap-2">
                          <div className="flex items-center gap-2 text-xs text-muted-foreground">
                            <Route className="w-3 h-3" />
                            <span>Route</span>
                          </div>
                          {/* 步行路线信息 */}
                          {itineraryRoutes[`${i-1}-${i}-walking`] && (
                            <div className="text-xs text-muted-foreground flex items-center gap-1">
                              <Footprints className="w-3 h-3" />
                              <span>{itineraryRoutes[`${i-1}-${i}-walking`].time} - {itineraryRoutes[`${i-1}-${i}-walking`].distance}</span>
                            </div>
                          )}
                          {/* 驾车路线信息 */}
                          {itineraryRoutes[`${i-1}-${i}-driving`] && (
                            <div className="text-xs text-muted-foreground flex items-center gap-1">
                              <Car className="w-3 h-3" />
                              <span>{itineraryRoutes[`${i-1}-${i}-driving`].time} - {itineraryRoutes[`${i-1}-${i}-driving`].distance}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                    <div className="flex items-center gap-3">
                      <div className={`w-9 h-9 rounded-full ${item.done ? "bg-primary/10" : "bg-accent/10"} flex items-center justify-center`}>
                        <MapPin className={`w-4 h-4 ${item.done ? "text-primary" : "text-accent"}`} />
                      </div>
                      <div>
                        <p className={`text-sm font-medium ${item.done ? "text-muted-foreground" : ""}`}>{item.place}</p>
                      </div>
                    </div>
                  </>
                ))}
                
                {/* Navigation Control Buttons */}
                <div className="mt-4 flex gap-2">
                  <button
                    className="flex-1 px-3 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors flex items-center justify-center gap-1"
                    onClick={startItineraryNavigation}
                  >
                    <Play className="w-4 h-4" />
                    <span>Start Navigation</span>
                  </button>
                </div>
              </>
            ) : (
              <div className="text-center py-4 text-muted-foreground">
                <p>Please enter start and end points, click Plan Route</p>
              </div>
            )}
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
