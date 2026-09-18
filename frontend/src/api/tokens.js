// ==============================|| TOKEN STORAGE ||============================== //

// Where the JWT pair issued by POST /auth/login lives between page loads.
//
// localStorage, not a cookie, because the client and the API are served from
// different origins in deployment (static bundle on S3/CloudFront, Django on
// EC2). A cookie would have to be SameSite=None; Secure and would drag CSRF
// handling into every write. A bearer token in a header has neither problem.
//
// The trade-off is honest and worth writing up in the report: localStorage is
// readable by any script running on the page, so a successful XSS can steal the
// token. That is why the access token lives 30 minutes (SIMPLE_JWT
// ACCESS_TOKEN_LIFETIME) rather than indefinitely, and why the API never
// accepts organisation_id from the client — a stolen token still cannot reach
// another tenant's data.

const ACCESS_KEY = 'worklink.access';
const REFRESH_KEY = 'worklink.refresh';
const USER_KEY = 'worklink.user';

// Private browsing and some embedded webviews throw on localStorage access
// rather than returning null, so every call is guarded. Losing the token means
// the user logs in again; an uncaught exception here would blank the whole app.
function safeGet(key) {
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

function safeSet(key, value) {
  try {
    if (value === null || value === undefined) {
      window.localStorage.removeItem(key);
    } else {
      window.localStorage.setItem(key, value);
    }
  } catch {
    // Storage unavailable. The session still works in memory for this tab.
  }
}

export function getAccessToken() {
  return safeGet(ACCESS_KEY);
}

export function getRefreshToken() {
  return safeGet(REFRESH_KEY);
}

// Cached so a reload can render the shell without waiting on GET /auth/me.
// Treated as a hint only: AuthContext always re-validates against the API,
// because anything in localStorage is user-editable and must never be trusted
// for authorisation decisions.
export function getCachedUser() {
  const raw = safeGet(USER_KEY);

  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function setTokens(tokens) {
  safeSet(ACCESS_KEY, tokens?.access ?? null);
  safeSet(REFRESH_KEY, tokens?.refresh ?? null);
}

export function setCachedUser(user) {
  safeSet(USER_KEY, user ? JSON.stringify(user) : null);
}

export function clearSession() {
  safeSet(ACCESS_KEY, null);
  safeSet(REFRESH_KEY, null);
  safeSet(USER_KEY, null);
}
