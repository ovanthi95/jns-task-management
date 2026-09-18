import PropTypes from 'prop-types';
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';

// project-imports
import { UNAUTHENTICATED_EVENT } from 'api/client';
import { clearSession, getAccessToken, getCachedUser, setCachedUser, setTokens } from 'api/tokens';
import * as api from 'api/worklink';

// ==============================|| AUTH CONTEXT ||============================== //

// Holds the signed-in user for the whole app. Three jobs:
//
//   1. On boot, decide whether the token in localStorage is still usable, by
//      asking the API rather than by trusting what is stored.
//   2. Expose login / register / logout so no view has to know about tokens.
//   3. Log out when the API client reports that refresh has failed.
//
// `user` comes from GET /auth/me and carries role_name, which is what drives
// the role-dependent UI. It is a convenience only: the server re-checks the
// caller's role on every request, so hiding a button here is never the control.

const AuthContext = createContext(null);

const initialState = {
  user: getCachedUser(),
  // Only "initialising" if there is a token worth validating. With no token the
  // app can render the login page immediately.
  initialising: Boolean(getAccessToken())
};

export function AuthProvider({ children }) {
  const [user, setUser] = useState(initialState.user);
  const [initialising, setInitialising] = useState(initialState.initialising);

  // Guards against setting state after the provider unmounts in React 19
  // StrictMode, which mounts effects twice in development.
  const mounted = useRef(true);

  const applySession = useCallback((payload) => {
    setTokens(payload.tokens);
    setCachedUser(payload.user);
    setUser(payload.user);
    return payload.user;
  }, []);

  const logout = useCallback(() => {
    // Client-side only. The API issues stateless JWTs with no server-side
    // session to destroy, which is what lets any instance behind the load
    // balancer serve any request. The trade-off is that an already-issued
    // access token stays valid until it expires — hence the 30-minute lifetime.
    clearSession();
    setUser(null);
  }, []);

  // Validate the stored token exactly once on boot.
  useEffect(() => {
    mounted.current = true;

    if (!getAccessToken()) {
      return undefined;
    }

    const controller = new AbortController();

    api
      .getMe(controller.signal)
      .then((freshUser) => {
        if (!mounted.current) {
          return;
        }
        setCachedUser(freshUser);
        setUser(freshUser);
      })
      .catch((error) => {
        if (error?.name === 'AbortError' || !mounted.current) {
          return;
        }
        // 401 after a failed refresh means the session is genuinely over. Any
        // other failure (API down, CORS) should not silently discard a token
        // that may still be good, so only 401/403 clear it.
        if (error?.status === 401 || error?.status === 403) {
          clearSession();
          setUser(null);
        }
      })
      .finally(() => {
        if (mounted.current) {
          setInitialising(false);
        }
      });

    return () => {
      mounted.current = false;
      controller.abort();
    };
  }, []);

  // The API client fires this when a refresh attempt fails.
  useEffect(() => {
    const handler = () => setUser(null);

    window.addEventListener(UNAUTHENTICATED_EVENT, handler);
    return () => window.removeEventListener(UNAUTHENTICATED_EVENT, handler);
  }, []);

  const login = useCallback(
    async (credentials) => {
      return applySession(await api.login(credentials));
    },
    [applySession]
  );

  const register = useCallback(
    async (details) => {
      return applySession(await api.register(details));
    },
    [applySession]
  );

  const value = useMemo(
    () => ({
      user,
      isAuthenticated: Boolean(user),
      initialising,
      role: user?.role_name ?? null,
      // Task and project creation are Manager/Admin only server-side
      // (IsManagerOrReadOnly). Mirrored here purely so the UI can explain
      // itself before the user hits a 403.
      canManage: ['Admin', 'Manager'].includes(user?.role_name),
      login,
      register,
      logout
    }),
    [user, initialising, login, register, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

AuthProvider.propTypes = { children: PropTypes.node };

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error('useAuth must be used inside <AuthProvider>.');
  }

  return context;
}

export default AuthContext;
