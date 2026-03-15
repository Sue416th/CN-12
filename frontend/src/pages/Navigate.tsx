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

const Navigate = () => {
  const location = useLocation();
  const locationState = (location.state || {}) as {
    day?: number;
    activities?: ActivityFromPlanner[];
  };

  const mapRef = useRef<HTMLDivElement | null>(null);
  const routeLineRef = useRef<any>(null);
  const watchIdRef = useRef<number | null>(null);
  const lastRouteUpdateRef = useRef<number>(0);

  const [map, setMap] = useState<any>(null);
  const [mapError, setMapError] = useState("");
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [mode, setMode] = useState<TravelMode>("walking");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<NavigationApiResponse["route"] | null>(null);
  const [navigationMode, setNavigationMode] = useState(false);
  const [currentLocation, setCurrentLocation] = useState<[number, number] | null>(null);
  const [itineraryRoutes, setItineraryRoutes] = useState<Record<string, NavigationApiResponse["route"]>>({});

  const itinerary: ItineraryItem[] = useMemo(() => {
    if (locationState.activities && locationState.activities.length > 0) {
      return locationState.activities.map((activity, index) => {
        const hour = 9 + index * 2;
        return {
          time: `${hour.toString().padStart(2, "0")}:00`,
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

    routeLineRef.current = line;
    map.add(line);
    map.setFitView([line]);
  };

  const setLocationMarker = (loc: [number, number], isCurrent = false) => {
    if (!map || !(window as any).AMap) return;
    const amapLib = (window as any).AMap;
    const marker = new amapLib.Marker({
      position: loc,
      title: isCurrent ? "Current Location" : "Destination",
    });
    map.add(marker);
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
        script.onload = () => resolve();
        script.onerror = () => reject(new Error(`Failed to load ${src}`));
        document.body.appendChild(script);
      });

    const initMap = async () => {
      try {
        await appendScript("amap-script", "https://webapi.amap.com/maps?v=2.0&key=b455605867e22ee43f90103bca82bbe8");
      } catch {
        if (!cancelled) setMapError("Failed to load map library.");
        return;
      }

      if (!(window as any).AMap) {
        if (!cancelled) setMapError("Map library not available.");
        return;
      }

      const amapLib = (window as any).AMap;
      if (!mapRef.current) return;

      amapInstance = new amapLib.Map(mapRef.current, {
        zoom: 12,
        center: [120.1551, 30.2741],
      });

      if (!cancelled) {
        setMap(amapInstance);
      }
    };

    initMap();

    return () => {
      cancelled = true;
      if (amapInstance) {
        try {
          amapInstance.destroy();
        } catch {}
      }
    };
  }, []);

  useEffect(() => {
    if (result?.path?.length) {
      drawRouteOnMap(result.path);
    }
  }, [result, map]);

  useEffect(() => {
    if (!navigationMode) {
      if (watchIdRef.current !== null) {
        navigator.geolocation.clearWatch(watchIdRef.current);
        watchIdRef.current = null;
      }
      return;
    }
    return () => {
      if (watchIdRef.current !== null) {
        navigator.geolocation.clearWatch(watchIdRef.current);
        watchIdRef.current = null;
      }
    };
  }, [navigationMode]);

  useEffect(() => {
    const fetchItineraryRoutes = async () => {
      if (itinerary.length < 2) return;
      const routes: Record<string, NavigationApiResponse["route"]> = {};
      for (let i = 1; i < itinerary.length; i++) {
        const startPlace = itinerary[i - 1].place;
        const endPlace = itinerary[i].place;
        try {
          routes[`${i - 1}-${i}-walking`] = await fetchRoute(startPlace, endPlace, "walking");
        } catch {
          routes[`${i - 1}-${i}-walking`] = { distance: "--", time: "--", steps: [], path: [] };
        }
        try {
          routes[`${i - 1}-${i}-driving`] = await fetchRoute(startPlace, endPlace, "driving");
        } catch {
          routes[`${i - 1}-${i}-driving`] = { distance: "--", time: "--", steps: [], path: [] };
        }
      }
      setItineraryRoutes(routes);
    };
    void fetchItineraryRoutes();
  }, [itinerary]);

  const fetchRoute = async (startValue: string, endValue: string, travelMode: TravelMode) => {
    const response = await fetch("http://127.0.0.1:3204/api/navigation/navigate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        start: startValue,
        end: endValue,
        mode: travelMode,
      }),
    });

    const data = (await response.json()) as NavigationApiResponse | { detail?: string };
    if (!response.ok || !("status" in data) || data.status !== "success") {
      throw new Error(extractErrorMessage(data, "Navigation service is temporarily unavailable."));
    }
    return data.route;
  };

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
      setError("Failed to fetch route. Please check the backend service and try again.");
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
        } catch {
          // ignore update errors
        }
      },
      () => {
        setError("Unable to retrieve your location.");
      },
      { enableHighAccuracy: true, maximumAge: 10000, timeout: 15000 }
    );
  };

  const startItineraryNavigation = () => {
    if (itinerary.length < 2) return;
    setError("");
    const nextIndex = itinerary.findIndex((item) => !item.done);
    const targetIndex = nextIndex <= 0 ? 1 : nextIndex;
    const fromPlace = itinerary[targetIndex - 1]?.place || itinerary[0].place;
    const toPlace = itinerary[targetIndex]?.place || itinerary[1].place;

    setStart(fromPlace);
    setEnd(toPlace);
    setMode("walking");
    setResult(null);
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

            <div className="mt-3 flex flex-wrap gap-2">
              <button
                onClick={handlePlanRoute}
                disabled={loading}
                className="inline-flex h-9 items-center gap-2 rounded-lg bg-primary px-3 text-sm font-medium text-primary-foreground disabled:opacity-60"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Route className="w-4 h-4" />}
                Plan Route
              </button>
              <button
                onClick={startRealtimeNavigation}
                disabled={!end.trim() || navigationMode}
                className="inline-flex h-9 items-center gap-2 rounded-lg bg-secondary px-3 text-sm font-medium text-secondary-foreground disabled:opacity-60"
              >
                <Play className="w-4 h-4" />
                Start Real-time Navigation
              </button>
              {navigationMode && (
                <button
                  onClick={() => setNavigationMode(false)}
                  className="inline-flex h-9 items-center gap-2 rounded-lg bg-destructive px-3 text-sm font-medium text-destructive-foreground"
                >
                  <X className="w-4 h-4" />
                  Stop Navigation
                </button>
              )}
            </div>

            {error && (
              <div className="mt-3 text-sm text-destructive">{error}</div>
            )}

            {result && (
              <div className="mt-4 rounded-xl bg-muted/50 p-4">
                <div className="flex items-center gap-2 text-sm">
                  <MapPin className="w-4 h-4 text-primary" />
                  <span className="font-medium">{modeLabel[mode]}</span>
                  <span className="text-muted-foreground">•</span>
                  <span>{result.distance}</span>
                  <span className="text-muted-foreground">•</span>
                  <span>{result.time}</span>
                </div>
              </div>
            )}
          </div>

          <div
            ref={mapRef}
            className="rounded-2xl bg-card shadow-sm border border-border/50 overflow-hidden"
            style={{ height: 420 }}
          />
          {mapError && (
            <div className="text-sm text-destructive">{mapError}</div>
          )}
        </div>

        <div className="xl:col-span-4 space-y-5">
          <div className="rounded-2xl bg-card p-5 shadow-sm border border-border/50">
            <h3 className="font-display font-semibold mb-4">Route Steps</h3>
            <div className="space-y-2 max-h-[280px] overflow-auto pr-1">
              {!result?.steps?.length ? (
                <div className="text-sm text-muted-foreground py-2">
                  Plan a route to see step-by-step instructions.
                </div>
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
                <div className="text-sm text-muted-foreground py-4">
                  No itinerary available. Please create a trip first.
                </div>
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
            {itinerary.length > 0 && (
              <button
                onClick={startItineraryNavigation}
                className="mt-4 inline-flex h-9 items-center gap-2 rounded-lg bg-primary px-3 text-sm font-medium text-primary-foreground"
              >
                <Play className="w-4 h-4" />
                Start Itinerary Navigation
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Navigate;
