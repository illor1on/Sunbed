import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { useCity } from "../city/CityContext";

import Login from "../pages/Login";
import Register from "../pages/Register";
import CitySelect from "../pages/CitySelect";
import BeachList from "../pages/BeachList";
import ProtectedRoute from "./ProtectedRoute";
import Profile from "../pages/Profile";
import Sunbeds from "../pages/Sunbeds";
import ActiveBookings from "../pages/ActiveBookings";
import BookingHistory from "../pages/BookingHistory";

import OwnerGuard from "../owner/OwnerGuard";
import OwnerDashboard from "../owner/OwnerDashboard";
import OwnerBeaches from "../owner/OwnerBeaches";
import OwnerBeach from "../owner/OwnerBeach";
import OwnerBookings from "../owner/OwnerBookings";
import OwnerPayment from "../owner/OwnerPayment";
import OwnerBeachCreate from "../owner/OwnerBeachCreate";
import OwnerPrices from "../owner/OwnerPrices";
import OwnerPriceCreate from "../owner/OwnerPriceCreate";
import OwnerPriceEdit from "../owner/OwnerPriceEdit";
import OwnerSunbeds from "../owner/OwnerSunbeds";
import OwnerSunbedCreate from "../owner/OwnerSunbedCreate";







export default function AppRouter() {
  const { user, loading } = useAuth();
  const { location } = useCity();

  // 🔴 КЛЮЧ: ничего не рендерим, пока auth не восстановился
  if (loading) {
    return null; // или loader
  }

  return (
    <Routes>
      <Route
      path="/profile"
      element={
        <ProtectedRoute>
          <Profile />
        </ProtectedRoute>
        }
      />

      <Route
        path="/beach/:id/sunbeds"
        element={
          <ProtectedRoute>
            <Sunbeds />
          </ProtectedRoute>
        }
      />


      {/* PUBLIC */}
      <Route
        path="/login"
        element={user ? <Navigate to="/city" replace /> : <Login />}
      />

      <Route
        path="/register"
        element={user ? <Navigate to="/city" replace /> : <Register />}
      />

      {/* CITY */}
      <Route
        path="/city"
        element={
          <ProtectedRoute>
            <CitySelect />
          </ProtectedRoute>
        }
      />

      {/* BEACHES */}
      <Route
        path="/beaches"
        element={
          <ProtectedRoute>
            {!location ? <Navigate to="/city" replace /> : <BeachList />}
          </ProtectedRoute>
        }
      />

      {/* FALLBACK */}
      <Route
        path="*"
        element={
          user ? <Navigate to="/city" replace /> : <Navigate to="/login" replace />
        }
      />

      <Route
        path="/active-bookings"
        element={
          <ProtectedRoute>
            <ActiveBookings />
          </ProtectedRoute>
        }
      />

       <Route
        path="/booking-history"
        element={
          <ProtectedRoute>
            <BookingHistory />
          </ProtectedRoute>
        }
      />

      <Route
        path="/owner"
        element={
          <ProtectedRoute>
            <OwnerGuard />
          </ProtectedRoute>
        }
      >
        <Route index element={<OwnerDashboard />} />
        <Route path="beaches" element={<OwnerBeaches />} />
        <Route path="beaches/:id" element={<OwnerBeach />} />
        <Route path="bookings" element={<OwnerBookings />} />
        <Route path="payment" element={<OwnerPayment />} />
        <Route path="/owner/beaches/new" element={<OwnerBeachCreate />} />
        <Route path="/owner/prices" element={<OwnerPrices />} />
        <Route path="/owner/prices/new" element={<OwnerPriceCreate />} />
        <Route path="/owner/prices/:id" element={<OwnerPriceEdit />} />
        <Route path="/owner/beaches/:id/sunbeds" element={<OwnerSunbeds />} />
        <Route path="/owner/beaches/:beachId/sunbeds/new" element={<OwnerSunbedCreate />} />



      </Route>

      
    </Routes>
  );
}
