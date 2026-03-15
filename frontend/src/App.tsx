import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AuthProvider, useAuth } from "@/context/AuthContext";
import Layout from "./components/Layout";
import Index from "./pages/Index";
import NavigatePage from "./pages/Navigate";
import Culture from "./pages/Culture";
import Profile from "./pages/Profile";
import ProfileSettings from "./pages/ProfileSettings";
import Auth from "./pages/Auth";
import AdminDashboard from "./pages/AdminDashboard";
import NotFound from "./pages/NotFound";
import TripPlanner from "./pages/TripPlanner";
import TripsList from "./pages/TripsList";
import TripDetail from "./pages/TripDetail";
import TripEvaluationResult from "./pages/TripEvaluationResult";
import TravelHistory from "./pages/TravelHistory";
import DestinationDetail from "./pages/DestinationDetail";

const queryClient = new QueryClient();

const ProtectedProfileRoute = () => {
  const { isLoggedIn, user } = useAuth();
  if (!isLoggedIn) {
    return <Navigate to="/auth" replace />;
  }
  if (user?.role === "admin") {
    return <Navigate to="/admin" replace />;
  }
  return <Profile />;
};

const ProtectedProfileSettingsRoute = () => {
  const { isLoggedIn, user } = useAuth();
  if (!isLoggedIn) {
    return <Navigate to="/auth" replace />;
  }
  if (user?.role === "admin") {
    return <Navigate to="/admin" replace />;
  }
  return <ProfileSettings />;
};

const ProtectedAdminRoute = () => {
  const { isLoggedIn, user } = useAuth();
  if (!isLoggedIn) {
    return <Navigate to="/auth" replace />;
  }
  if (user?.role !== "admin") {
    return <Navigate to="/" replace />;
  }
  return <AdminDashboard />;
};

const ProtectedUserRoute = ({ children }: { children: JSX.Element }) => {
  const { isLoggedIn, user } = useAuth();
  if (!isLoggedIn) {
    return <Navigate to="/auth" replace />;
  }
  if (user?.role !== "user") {
    return <Navigate to="/admin" replace />;
  }
  return children;
};

const AuthRoute = () => {
  const { isLoggedIn, user } = useAuth();
  if (!isLoggedIn) {
    return <Auth />;
  }
  if (user?.role === "admin") {
    return <Navigate to="/admin" replace />;
  }
  return <Navigate to="/" replace />;
};

const App = () => (
  <QueryClientProvider client={queryClient}>
    <AuthProvider>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Routes>
            <Route element={<Layout />}>
              <Route path="/" element={<Index />} />
              <Route path="/navigate" element={<NavigatePage />} />
              <Route path="/culture" element={<Culture />} />
              <Route path="/auth" element={<AuthRoute />} />
              <Route path="/profile" element={<ProtectedProfileRoute />} />
              <Route path="/profile/settings" element={<ProtectedProfileSettingsRoute />} />
              <Route path="/admin" element={<ProtectedAdminRoute />} />
              <Route
                path="/trip-planner"
                element={(
                  <ProtectedUserRoute>
                    <TripPlanner />
                  </ProtectedUserRoute>
                )}
              />
              <Route
                path="/trips"
                element={(
                  <ProtectedUserRoute>
                    <TripsList />
                  </ProtectedUserRoute>
                )}
              />
              <Route
                path="/trip-detail/:tripId"
                element={(
                  <ProtectedUserRoute>
                    <TripDetail />
                  </ProtectedUserRoute>
                )}
              />
              <Route
                path="/trip-evaluation/:tripId"
                element={(
                  <ProtectedUserRoute>
                    <TripEvaluationResult />
                  </ProtectedUserRoute>
                )}
              />
              <Route
                path="/travel-history"
                element={(
                  <ProtectedUserRoute>
                    <TravelHistory />
                  </ProtectedUserRoute>
                )}
              />
              <Route path="/destination/:destinationId" element={<DestinationDetail />} />
            </Route>
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </AuthProvider>
  </QueryClientProvider>
);

export default App;
