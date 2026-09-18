import { Navigate, Outlet, useLocation } from 'react-router-dom';

// project-imports
import Loader from 'components/Loader';
import { useAuth } from 'contexts/AuthContext';

// ==============================|| ROUTE GUARD ||============================== //

// Wraps the authenticated part of the router. Two things it is NOT:
//
//   * a security control — the API rejects every unauthenticated request on its
//     own, and anyone can edit client-side state. This only saves the user from
//     landing on a page that would be empty and full of errors.
//   * a redirect on first paint — while the boot-time GET /auth/me is still in
//     flight, `initialising` is true and we render the loader instead, so a
//     signed-in user reloading a deep link is not bounced to /login and back.

export default function RequireAuth() {
  const { isAuthenticated, initialising } = useAuth();
  const location = useLocation();

  if (initialising) {
    return <Loader />;
  }

  if (!isAuthenticated) {
    // `state.from` lets the login page send the user back where they were
    // heading instead of always dumping them on the dashboard.
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <Outlet />;
}
