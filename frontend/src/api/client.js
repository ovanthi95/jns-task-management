// ==============================|| WORKLINK API CLIENT ||============================== //

// One place that knows how to talk to the Django REST API: base URL, bearer
// token, silent token refresh, and turning DRF error bodies into something a
// form can render.
//
// Everything else in the app calls `api.*` from api/worklink.js and never
// touches fetch directly.

import { clearSession, getAccessToken, getRefreshToken, setTokens } from './tokens';

// VITE_API_BASE_URL is set per environment in .env / .env.production. The
// fallback is the Django development server so `npm start` works with no
// configuration at all.
const RAW_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1';

// A trailing slash on the base would produce '//projects' after joining.
export const API_BASE_URL = RAW_BASE.replace(/\/+$/, '');

// Fired when the refresh token is gone or rejected. AuthContext listens for it
// and clears the session. Using a DOM event rather than an import keeps this
// module free of React and avoids a circular dependency between the client and
// the context that uses it.
export const UNAUTHENTICATED_EVENT = 'worklink:unauthenticated';

// IMPORTANT: the Django URLconf registers these routes WITHOUT a trailing
// slash (`path("projects", ...)`), so '/projects/' is a 404, not a redirect to
// '/projects'. Never append one when building a path.
function buildUrl(path) {
  return `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`;
}

// ==============================|| ERRORS ||============================== //

/**
 * A failed API call, normalised.
 *
 * `fieldErrors` maps a serializer field name to a single display string, which
 * is the shape react-bootstrap's <Form.Control.Feedback> wants. `message` is
 * always safe to show on its own when there is no field to attach it to.
 */
export class ApiError extends Error {
  constructor(message, { status = 0, fieldErrors = {}, body = null } = {}) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.fieldErrors = fieldErrors;
    this.body = body;
  }
}

// DRF emits several shapes depending on where validation failed:
//
//   {"detail": "Authentication credentials were not provided."}   permissions
//   {"title": ["A task must have a title."]}                      field errors
//   {"non_field_errors": ["Incorrect email or password."]}        serializer-level
//   ["Something went wrong."]                                     raise on a list
//
// All four are flattened here so callers only ever handle one.
function parseErrorBody(body, status) {
  const fieldErrors = {};
  let message = '';

  const flatten = (value) => {
    if (Array.isArray(value)) {
      return value.map(flatten).filter(Boolean).join(' ');
    }
    if (value && typeof value === 'object') {
      return Object.values(value).map(flatten).filter(Boolean).join(' ');
    }
    return value == null ? '' : String(value);
  };

  if (typeof body === 'string') {
    message = body;
  } else if (Array.isArray(body)) {
    message = flatten(body);
  } else if (body && typeof body === 'object') {
    Object.entries(body).forEach(([key, value]) => {
      const text = flatten(value);

      if (key === 'detail' || key === 'non_field_errors') {
        message = message ? `${message} ${text}` : text;
      } else {
        fieldErrors[key] = text;
      }
    });

    // A pure field-error response still needs something to show in a banner.
    if (!message) {
      const first = Object.entries(fieldErrors)[0];
      message = first ? `${first[0]}: ${first[1]}` : '';
    }
  }

  if (!message) {
    message = `Request failed with status ${status}.`;
  }

  return { message: message.trim(), fieldErrors };
}

// ==============================|| TOKEN REFRESH ||============================== //

// Single-flight. If three requests 401 at the same moment they must not fire
// three refreshes — the second and third would race, and SimpleJWT with token
// rotation enabled would invalidate the pair. They all await this one promise.
let refreshInFlight = null;

async function refreshAccessToken() {
  if (refreshInFlight) {
    return refreshInFlight;
  }

  const refresh = getRefreshToken();

  if (!refresh) {
    return null;
  }

  refreshInFlight = (async () => {
    try {
      const response = await fetch(buildUrl('/auth/refresh'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh })
      });

      if (!response.ok) {
        return null;
      }

      const data = await response.json();

      if (!data?.access) {
        return null;
      }

      // ROTATE_REFRESH_TOKENS is off in the settings patch, so the response
      // carries only `access` and the existing refresh token stays valid. The
      // `?? refresh` keeps this correct if the team turns rotation on later.
      setTokens({ access: data.access, refresh: data.refresh ?? refresh });
      return data.access;
    } catch {
      // Network failure, not an auth failure. Returning null sends the caller
      // down the same path as a rejected token, which logs the user out — a
      // conservative choice, and the request would have failed anyway.
      return null;
    } finally {
      refreshInFlight = null;
    }
  })();

  return refreshInFlight;
}

function giveUp() {
  clearSession();
  window.dispatchEvent(new CustomEvent(UNAUTHENTICATED_EVENT));
}

// ==============================|| REQUEST ||============================== //

async function readBody(response) {
  if (response.status === 204) {
    return null;
  }

  const contentType = response.headers.get('content-type') || '';

  if (contentType.includes('application/json')) {
    try {
      return await response.json();
    } catch {
      return null;
    }
  }

  // Django's own 500 page, an nginx 502, or the browsable API's HTML all land
  // here. Returning the text means the error banner says something real
  // instead of "undefined".
  try {
    return await response.text();
  } catch {
    return null;
  }
}

/**
 * Make one authenticated request against the WorkLink API.
 *
 * @param {string} path     e.g. '/projects/2/tasks' (no trailing slash)
 * @param {object} options  method, body (plain object, JSON-encoded here),
 *                          params (query string), auth (false for public
 *                          endpoints), signal (AbortController)
 * @returns {Promise<any>}  the parsed JSON body
 * @throws  {ApiError}
 */
export async function apiFetch(path, options = {}) {
  const { method = 'GET', body, params, auth = true, signal, retryOn401 = true } = options;

  let url = buildUrl(path);

  if (params) {
    // Drop empty values so '?status_id=' is never sent — Django would try to
    // filter on the empty string and return a 400.
    const search = new URLSearchParams();

    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        search.append(key, value);
      }
    });

    const query = search.toString();

    if (query) {
      url += `?${query}`;
    }
  }

  const headers = { Accept: 'application/json' };

  if (body !== undefined) {
    headers['Content-Type'] = 'application/json';
  }

  if (auth) {
    const access = getAccessToken();

    if (access) {
      // AUTH_HEADER_TYPES is ('Bearer',) in SIMPLE_JWT, so the prefix matters.
      headers.Authorization = `Bearer ${access}`;
    }
  }

  let response;

  try {
    response = await fetch(url, {
      method,
      headers,
      signal,
      body: body === undefined ? undefined : JSON.stringify(body)
    });
  } catch (error) {
    // fetch only rejects for network-level failures: the API is down, DNS
    // fails, or CORS blocked the request before it was sent. Worth naming CORS
    // explicitly because it is the most likely cause the first time the
    // deployed client talks to the deployed API.
    if (error?.name === 'AbortError') {
      throw error;
    }

    throw new ApiError(
      `Could not reach the API at ${API_BASE_URL}. Check that the server is running and that this origin is listed in CORS_ALLOWED_ORIGINS.`,
      {
        status: 0
      }
    );
  }

  // Access token expired. Refresh once, then replay the original request.
  if (response.status === 401 && auth && retryOn401) {
    const access = await refreshAccessToken();

    if (access) {
      return apiFetch(path, { ...options, retryOn401: false });
    }

    giveUp();
  }

  const payload = await readBody(response);

  if (!response.ok) {
    const { message, fieldErrors } = parseErrorBody(payload, response.status);

    throw new ApiError(message, { status: response.status, fieldErrors, body: payload });
  }

  return payload;
}

// Every list endpoint that paginates returns
// {count, next, previous, results}; the lookups set pagination_class = None and
// return a bare array. This accepts either so callers can stop caring which.
export function unwrapList(payload) {
  if (Array.isArray(payload)) {
    return payload;
  }

  return payload?.results ?? [];
}
