import { useEffect, useMemo, useRef, useState } from "react";
import { motion } from "framer-motion";
import {
  Navigation,
  MapPin,
  Clock,
  Route,
  Loader2,
  Play,
  X,
  Footprints,
  Car,
} from "lucide-react";
import { useLocation } from "react-router-dom";

type TravelMode = "driving" | "walking";

type NavigationApiResponse = {
  status: "success" | "error";
  route: {
    distance: string;
    time: string;
    steps: string[];
    path: number[][];
  };
};

type ActivityFromPlanner = {
  name: string;
  category?: string;
};

type ItineraryItem = {
  time: string;
  place: string;
  done: boolean;
  category?: string;
};

const modeLabel: Record<TravelMode, string> = {
  driving: "Driving",
  walking: "Walking",
};

const extractErrorMessage = (payload: unknown, fallback: string) => {
  if (
    payload &&
    typeof payload === "object" &&
    "detail" in payload &&
    typeof (payload as { detail?: unknown }).detail === "string"
  ) {
    return (payload as { detail: string }).detail;
  }
  return fallback;
};

const isQuotaExceededError = (message: string) =>
  message.includes("CUQPS_HAS_EXCEEDED_THE_LIMIT") ||
  message.includes("AMAP_QUOTA_EXCEEDED") ||
  message.toLowerCase().includes("quota exceeded");

const toFriendlyNavigationError = (message: string) => {
  if (isQuotaExceededError(message)) {
    return "Navigation API quota exceeded. Please retry later.";
  }
  if (message.includes("起点解析失败")) {
    return "Start point could not be resolved. Please enter a clearer address.";
  }
  if (message.includes("终点解析失败")) {
    return "Destination could not be resolved. Please enter a clearer address.";
  }
  return message;
};

const Navigate = () => {
  const location = useLocation();
  const locationState = (location.state || {}) as {
    day?: number;
    date?: string;
    activities?: ActivityFromPlanner[];
    city?: string;
  };

  const mapRef = useRef<HTMLDivElement>(null);
  const routeLineRef = useRef<any>(null);
  const currentMarkerRef = useRef<any>(null);
  const initialMarkerRef = useRef<any>(null);
  const routeStartMarkerRef = useRef<any>(null);
  const routeEndMarkerRef = useRef<any>(null);
  const watchIdRef = useRef<number | null>(null);
  const lastRouteUpdateRef = useRef(0);
  const routeCacheRef = useRef<Record<string, NavigationApiResponse["route"]>>({});

  const [map, setMap] = useState<any>(null);
  const [mapError, setMapError] = useState("");
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [mode, setMode] = useState<TravelMode>("walking");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [locationError, setLocationError] = useState("");
  const [result, setResult] = useState<NavigationApiResponse["route"] | null>(null);
  const [navigationMode, setNavigationMode] = useState(false);
  const [currentLocation, setCurrentLocation] = useState<[number, number] | null>(null);
  const [itineraryRoutes, setItineraryRoutes] = useState<Record<string, NavigationApiResponse["route"]>>({});

  const itinerary = useMemo<ItineraryItem[]>(() => {
    if (locationState.activities?.length) {
      return locationState.activities.map((activity, index) => {
        const startHour = 9 + Math.floor((index * 150) / 60);
        const startMinute = (index * 30) % 60;
        return {
          time: `${String(startHour).padStart(2, "0")}:${String(startMinute).padStart(2, "0")}`,
          place: activity.name,
          done: index === 0,
          category: activity.category,
        };
      });
    }
    return [];
  }, [locationState.activities]);

  const previewSteps = useMemo(() => {
    if (!result?.steps?.length) return [];
    return result.steps.slice(0, 10);
  }, [result]);

  const drawRouteOnMap = (path: number[][]) => {
    if (!map || !(window as any).AMap || !path?.length) return;

    const amapLib = (window as any).AMap;
    if (routeLineRef.current) {
      map.remove(routeLineRef.current);
      routeLineRef.current = null;
    }

    const line = new amapLib.Polyline({
      path,
      strokeColor: "#3366FF",
      strokeWeight: 5,
      strokeOpacity: 0.85,
    });
    line.setMap(map);
    routeLineRef.current = line;

    if (routeStartMarkerRef.current) {
      map.remove(routeStartMarkerRef.current);
      routeStartMarkerRef.current = null;
    }
    if (routeEndMarkerRef.current) {
      map.remove(routeEndMarkerRef.current);
      routeEndMarkerRef.current = null;
    }

    const startPoint = path[0];
    const endPoint = path[path.length - 1];
    if (startPoint && endPoint) {
      const startMarker = new amapLib.Marker({
        position: startPoint,
        content:
          '<div style="width:24px;height:24px;border-radius:50%;background:#16a34a;color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:12px;box-shadow:0 2px 6px rgba(0,0,0,0.25)">S</div>',
      });
      const endMarker = new amapLib.Marker({
        position: endPoint,
        content:
          '<div style="width:24px;height:24px;border-radius:50%;background:#dc2626;color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:12px;box-shadow:0 2px 6px rgba(0,0,0,0.25)">E</div>',
      });
      startMarker.setMap(map);
      endMarker.setMap(map);
      routeStartMarkerRef.current = startMarker;
      routeEndMarkerRef.current = endMarker;
    }

    map.setFitView([line]);
  };

  const setLocationMarker = (loc: [number, number], isRealtime: boolean) => {
    if (!map || !(window as any).AMap) return;
    const amapLib = (window as any).AMap;

    if (isRealtime) {
      if (currentMarkerRef.current) {
        map.remove(currentMarkerRef.current);
        currentMarkerRef.current = null;
      }
    } else {
      if (initialMarkerRef.current) {
        map.remove(initialMarkerRef.current);
        initialMarkerRef.current = null;
      }
    }

    const marker = new amapLib.Marker({
      position: loc,
      icon: new amapLib.Icon({
        size: new amapLib.Size(25, 25),
        image: isRealtime
          ? "https://a.amap.com/jsapi_demos/static/demo-center/icons/poi-marker-blue.png"
          : "https://a.amap.com/jsapi_demos/static/demo-center/icons/poi-marker-red.png",
        imageSize: new amapLib.Size(25, 25),
      }),
    });
    marker.setMap(map);

    if (isRealtime) {
      currentMarkerRef.current = marker;
    } else {
      initialMarkerRef.current = marker;
    }
  };

  const locateCurrentPosition = (amapInstance: any, amapLib: any) => {
    if (!navigator.geolocation) {
      setLocationError("Browser geolocation is unavailable.");
      return;
    }

    const applyLocation = (loc: [number, number]) => {
      setCurrentLocation(loc);
      amapInstance.setCenter(loc);
      // Keep same behavior as master: place initial current-position marker on refresh.
      if (initialMarkerRef.current) {
        amapInstance.remove(initialMarkerRef.current);
        initialMarkerRef.current = null;
      }
      const marker = new amapLib.Marker({
        position: loc,
        icon: new amapLib.Icon({
          size: new amapLib.Size(25, 25),
          image: "https://a.amap.com/jsapi_demos/static/demo-center/icons/poi-marker-red.png",
          imageSize: new amapLib.Size(25, 25),
        }),
      });
      marker.setMap(amapInstance);
      initialMarkerRef.current = marker;
      setLocationError("");
    };

    navigator.geolocation.getCurrentPosition(
      (position) => {
        applyLocation([position.coords.longitude, position.coords.latitude]);
      },
      () => {
        // Fallback: some devices resolve location only through watchPosition.
        const tempWatchId = navigator.geolocation.watchPosition(
          (position) => {
            applyLocation([position.coords.longitude, position.coords.latitude]);
            navigator.geolocation.clearWatch(tempWatchId);
          },
          () => {
            setLocationError("Unable to get current location. Please allow location permission.");
          },
          {
            enableHighAccuracy: true,
            timeout: 20000,
            maximumAge: 0,
          },
        );
      },
      {
        enableHighAccuracy: true,
        timeout: 15000,
        maximumAge: 0,
      },
    );
  };

  const fetchRoute = async (startValue: string, endValue: string, travelMode: TravelMode) => {
    const cityHint = String(locationState.city || "").trim();
    const cacheKey = `${travelMode}::${startValue}::${endValue}::${cityHint}`;
    if (routeCacheRef.current[cacheKey]) {
      return routeCacheRef.current[cacheKey];
    }

    const response = await fetch("http://127.0.0.1:3204/api/navigation/navigate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        start: startValue,
        end: endValue,
        mode: travelMode,
        city: cityHint || undefined,
      }),
    });

    const data = (await response.json()) as NavigationApiResponse | { detail?: string };
    if (!response.ok || !("status" in data) || data.status !== "success") {
      const rawError = extractErrorMessage(data, "Navigation service is temporarily unavailable.");
      throw new Error(toFriendlyNavigationError(rawError));
    }
    routeCacheRef.current[cacheKey] = data.route;
    return data.route;
  };

  useEffect(() => {
    if (!mapRef.current) return;
    let cancelled = false;
    let amapInstance: any = null;

    const appendScript = (id: string, src: string) =>
      new Promise<void>((resolve, reject) => {
        const existing = document.getElementById(id) as HTMLScriptElement | null;
        if (existing) {
          if ((window as any).AMap) {
            resolve();
            return;
          }
          existing.addEventListener("load", () => resolve(), { once: true });
          existing.addEventListener("error", () => reject(new Error(`Failed to load ${src}`)), { once: true });
          return;
        }

        const script = document.createElement("script");
        script.id = id;
        script.src = src;
        script.async = true;
        script.defer = true;
        script.onload = () => resolve();
        script.onerror = () => reject(new Error(`Failed to load ${src}`));
        document.head.appendChild(script);
      });

    const waitForAMap = async () => {
      if ((window as any).AMap) return (window as any).AMap;

      await appendScript(
        "amap-js-sdk",
        "https://webapi.amap.com/maps?v=2.0&key=5b283853affcc142e0863c2acd2ed2c8",
      );
      await appendScript("amap-ui-sdk", "https://webapi.amap.com/ui/1.1/main.js");

      return new Promise<any>((resolve, reject) => {
        const startedAt = Date.now();
        const poll = () => {
          if ((window as any).AMap) {
            resolve((window as any).AMap);
            return;
          }
          if (Date.now() - startedAt > 15000) {
            reject(new Error("AMap SDK timeout"));
            return;
          }
          setTimeout(poll, 250);
        };
        poll();
      });
    };

    setMapError("");

    void (async () => {
      try {
        const amapLib = await waitForAMap();
        if (cancelled || !mapRef.current) return;

        amapInstance = new amapLib.Map(mapRef.current, {
          zoom: 12,
          center: [100.199716, 25.680272],
          viewMode: "2D",
          mapStyle: "amap://styles/normal",
        });
        amapLib.plugin(["AMap.Scale", "AMap.ToolBar"], () => {
          amapInstance.addControl(new amapLib.Scale());
          amapInstance.addControl(new amapLib.ToolBar());
        });
        // Ensure base tile layer is attached (avoids blank grid in some environments).
        const baseLayer = new amapLib.TileLayer();
        amapInstance.add(baseLayer);

        setMap(amapInstance);
        locateCurrentPosition(amapInstance, amapLib);
      } catch (_error) {
        if (!cancelled) {
          setMapError("Map SDK failed to load. Please check network and refresh.");
        }
      }
    })();

    return () => {
      cancelled = true;
      if (watchIdRef.current !== null) {
        navigator.geolocation.clearWatch(watchIdRef.current);
        watchIdRef.current = null;
      }
      if (amapInstance) {
        amapInstance.destroy();
      }
      routeStartMarkerRef.current = null;
      routeEndMarkerRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!result?.path?.length) return;
    drawRouteOnMap(result.path);
  }, [map, result]);

  useEffect(() => {
    const loadItineraryRoutes = async () => {
      if (itinerary.length < 2) return;
      const routes: Record<string, NavigationApiResponse["route"]> = {};
      const maxSegments = Math.min(itinerary.length - 1, 2);
      let quotaHit = false;
      for (let i = 0; i < maxSegments; i += 1) {
        if (quotaHit) break;
        const startPlace = itinerary[i].place;
        const endPlace = itinerary[i + 1].place;
        try {
          routes[`${i}-${i + 1}-walking`] = await fetchRoute(startPlace, endPlace, "walking");
        } catch (e) {
          const msg = e instanceof Error ? e.message : String(e);
          if (isQuotaExceededError(msg)) {
            quotaHit = true;
            setError("Navigation API quota exceeded. Itinerary preview paused.");
          }
          // Skip this segment when API fails.
        }
        if (quotaHit) break;
        try {
          routes[`${i}-${i + 1}-driving`] = await fetchRoute(startPlace, endPlace, "driving");
        } catch (e) {
          const msg = e instanceof Error ? e.message : String(e);
          if (isQuotaExceededError(msg)) {
            quotaHit = true;
            setError("Navigation API quota exceeded. Itinerary preview paused.");
          }
          // Skip this segment when API fails.
        }
      }
      setItineraryRoutes(routes);
    };

    void loadItineraryRoutes();
  }, [itinerary]);

  const handlePlanRoute = async () => {
    if (!start.trim() || !end.trim()) {
      setError("Please enter both start and destination.");
      return;
    }

    setLoading(true);
    setError("");
    try {
      const route = await fetchRoute(start.trim(), end.trim(), mode);
      setResult(route);
    } catch (requestError) {
      console.error(requestError);
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Failed to fetch route. Please check the backend service and try again.",
      );
    } finally {
      setLoading(false);
    }
  };

  const startRealtimeNavigation = () => {
    if (!end.trim()) {
      setError("Please enter destination first.");
      return;
    }
    if (!navigator.geolocation) {
      setError("Geolocation is not supported by this browser.");
      return;
    }

    setNavigationMode(true);
    setError("");

    watchIdRef.current = navigator.geolocation.watchPosition(
      async (position) => {
        if (!map || !(window as any).AMap) return;

        const loc: [number, number] = [position.coords.longitude, position.coords.latitude];
        setCurrentLocation(loc);
        setLocationMarker(loc, true);
        map.setCenter(loc);

        const now = Date.now();
        if (now - lastRouteUpdateRef.current < 5000) return;
        lastRouteUpdateRef.current = now;

        try {
          const dynamicStart = `${loc[0]},${loc[1]}`;
          const route = await fetchRoute(dynamicStart, end.trim(), mode);
          setResult(route);
          drawRouteOnMap(route.path);
        } catch {
          // Keep last route on transient errors.
        }
      },
      () => {
        setError("Failed to get real-time location.");
      },
      {
        enableHighAccuracy: false,
        timeout: 10000,
        maximumAge: 30000,
      },
    );

    // Immediately plan current-location -> destination once user starts navigation.
    if (currentLocation) {
      const dynamicStart = `${currentLocation[0]},${currentLocation[1]}`;
      void fetchRoute(dynamicStart, end.trim(), mode)
        .then((route) => {
          setResult(route);
          drawRouteOnMap(route.path);
        })
        .catch(() => {
          // Keep UI responsive on first attempt failure.
        });
    }
  };

  const stopRealtimeNavigation = () => {
    setNavigationMode(false);
    if (watchIdRef.current !== null) {
      navigator.geolocation.clearWatch(watchIdRef.current);
      watchIdRef.current = null;
    }
    if (currentMarkerRef.current && map) {
      map.remove(currentMarkerRef.current);
      currentMarkerRef.current = null;
    }
  };

  const startItineraryNavigation = async () => {
    if (itinerary.length < 2) return;
    setError("");
    const nextIndex = itinerary.findIndex((item) => !item.done);
    const targetIndex = nextIndex <= 0 ? 1 : nextIndex;
    const fromPlace = itinerary[targetIndex - 1]?.place || itinerary[0].place;
    const toPlace = itinerary[targetIndex]?.place || itinerary[1].place;

    setStart(fromPlace);
    setEnd(toPlace);
    setMode("walking");

    try {
      setLoading(true);
      const route = await fetchRoute(fromPlace, toPlace, "walking");
      setResult(route);
    } catch {
      setError("Failed to get itinerary route.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container max-w-7xl mx-auto px-6 py-8 space-y-6">
      <div>
        <h1 className="text-2xl font-display font-bold">Live Navigation</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Plan routes, track live position, and monitor itinerary segment travel times.
        </p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-5 items-start">
        <div className="xl:col-span-8 space-y-5">
          <div className="rounded-2xl bg-card p-4 md:p-5 shadow-sm border border-border/50">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <input
                value={start}
                onChange={(event) => setStart(event.target.value)}
                placeholder="Start point"
                className="h-10 rounded-lg border border-border bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-primary/20"
              />
              <input
                value={end}
                onChange={(event) => setEnd(event.target.value)}
                placeholder="Destination"
                className="h-10 rounded-lg border border-border bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-primary/20"
              />
              <select
                value={mode}
                onChange={(event) => setMode(event.target.value as TravelMode)}
                className="h-10 rounded-lg border border-border bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-primary/20"
              >
                <option value="driving">Driving</option>
                <option value="walking">Walking</option>
              </select>
            </div>

            <div className="mt-4 flex flex-wrap items-center gap-2.5">
              <button
                onClick={handlePlanRoute}
                disabled={loading}
                className="inline-flex h-10 items-center gap-2 rounded-lg bg-primary px-4 text-sm font-medium text-primary-foreground disabled:opacity-60"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Navigation className="w-4 h-4" />}
                Plan Route
              </button>
              {!navigationMode ? (
                <button
                  onClick={startRealtimeNavigation}
                  className="inline-flex h-10 items-center gap-2 rounded-lg bg-emerald-600 px-4 text-sm font-medium text-white"
                >
                  <Play className="w-4 h-4" />
                  Start Navigation
                </button>
              ) : (
                <button
                  onClick={stopRealtimeNavigation}
                  className="inline-flex h-10 items-center gap-2 rounded-lg bg-red-600 px-4 text-sm font-medium text-white"
                >
                  <X className="w-4 h-4" />
                  Stop Navigation
                </button>
              )}
              <button
                onClick={() => {
                  const amapLib = (window as any).AMap;
                  if (map && amapLib) {
                    locateCurrentPosition(map, amapLib);
                  }
                }}
                className="inline-flex h-10 items-center gap-2 rounded-lg bg-slate-600 px-4 text-sm font-medium text-white"
              >
                Locate Me
              </button>
            </div>

            {(error || locationError) && (
              <div className="mt-3 rounded-lg border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive space-y-1">
                {error ? <p>{error}</p> : null}
                {locationError ? <p>{locationError}</p> : null}
              </div>
            )}
          </div>

          <div className="relative h-[430px] lg:h-[520px] rounded-2xl bg-secondary border border-border/50 shadow-sm overflow-hidden">
            <div ref={mapRef} className="absolute inset-0" />
            {!map || mapError ? (
              <div className="absolute inset-0 flex items-center justify-center text-center z-10 px-6 pointer-events-none">
                <div>
                  <Navigation className="w-14 h-14 text-primary mx-auto mb-3" />
                  {mapError ? (
                    <>
                      <p className="text-lg font-semibold">Map Unavailable</p>
                      <p className="text-sm text-destructive mt-1">{mapError}</p>
                    </>
                  ) : (
                    <>
                      <p className="text-muted-foreground">Loading map...</p>
                      <p className="text-sm text-muted-foreground mt-1">Please wait for AMap SDK initialization.</p>
                    </>
                  )}
                </div>
              </div>
            ) : null}
          </div>
        </div>

        <div className="xl:col-span-4 space-y-5 xl:sticky xl:top-20">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-2xl bg-card p-5 shadow-sm border border-border/50"
          >
            <h3 className="font-display font-semibold mb-4">Current Route</h3>
            <div className="flex items-center gap-3 mb-3">
              <div className="w-9 h-9 rounded-full bg-primary/10 flex items-center justify-center">
                <MapPin className="w-4 h-4 text-primary" />
              </div>
              <div>
                <p className="text-sm font-medium">{start || "Start point"}</p>
                <p className="text-xs text-muted-foreground">Current location</p>
              </div>
            </div>
            <div className="border-l-2 border-dashed border-primary/30 ml-4 pl-6 py-2">
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Route className="w-3 h-3" />
                <span>
                  {result ? `${modeLabel[mode]} • ${result.time} • ${result.distance}` : "Waiting for route planning..."}
                </span>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-full bg-accent/10 flex items-center justify-center">
                <MapPin className="w-4 h-4 text-accent" />
              </div>
              <div>
                <p className="text-sm font-medium">{end || "Destination"}</p>
                <p className="text-xs text-muted-foreground">Next stop</p>
              </div>
            </div>
          </motion.div>

          <div className="rounded-2xl bg-card p-5 shadow-sm border border-border/50">
            <h3 className="font-display font-semibold mb-4">Navigation Steps</h3>
            <div className="space-y-2.5 max-h-[280px] overflow-auto pr-1">
              {!previewSteps.length ? (
                <p className="text-sm text-muted-foreground">No step instructions yet. Plan a route first.</p>
              ) : (
                previewSteps.map((step, index) => (
                  <motion.div
                    key={`${step}-${index}`}
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.04 }}
                    className="flex items-start gap-3 p-3 rounded-lg hover:bg-muted/50 transition-colors"
                  >
                    <div className="w-2.5 h-2.5 rounded-full mt-1.5 bg-primary flex-shrink-0" />
                    <Clock className="w-3.5 h-3.5 text-muted-foreground mt-0.5" />
                    <span className="text-sm">{step}</span>
                  </motion.div>
                ))
              )}
            </div>
          </div>

          <div className="rounded-2xl bg-card p-5 shadow-sm border border-border/50">
            <h3 className="font-display font-semibold mb-4">Today's Itinerary Routes</h3>
            <div className="space-y-3 max-h-[280px] overflow-auto pr-1">
              {itinerary.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No itinerary loaded yet. Open Trip Detail and click Start Navigation to load today's route stops.
                </p>
              ) : (
                itinerary.map((item, i) => (
                  <div key={`${item.place}-${i}`}>
                    {i > 0 ? (
                      <div className="mb-2 rounded-md bg-muted/40 p-2 text-xs text-muted-foreground">
                        <div className="flex items-center gap-2">
                          <Footprints className="w-3 h-3" />
                          <span>
                            Walking: {itineraryRoutes[`${i - 1}-${i}-walking`]?.time || "--"} /{" "}
                            {itineraryRoutes[`${i - 1}-${i}-walking`]?.distance || "--"}
                          </span>
                        </div>
                        <div className="mt-1 flex items-center gap-2">
                          <Car className="w-3 h-3" />
                          <span>
                            Driving: {itineraryRoutes[`${i - 1}-${i}-driving`]?.time || "--"} /{" "}
                            {itineraryRoutes[`${i - 1}-${i}-driving`]?.distance || "--"}
                          </span>
                        </div>
                      </div>
                    ) : null}
                    <div className="flex items-center gap-2">
                      <Clock className="w-3.5 h-3.5 text-muted-foreground" />
                      <span className="text-xs text-muted-foreground w-12">{item.time}</span>
                      <span className="text-sm">{item.place}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
            <button
              onClick={startItineraryNavigation}
              disabled={itinerary.length < 2}
              className="mt-4 inline-flex h-9 items-center gap-2 rounded-lg bg-primary px-3 text-sm font-medium text-primary-foreground disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Play className="w-4 h-4" />
              Start Itinerary Navigation
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Navigate;
