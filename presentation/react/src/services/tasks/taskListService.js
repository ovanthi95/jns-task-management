// API 07 service - GET /api/projects/:projectId/tasks
// Owner: Edward
//
// Same shape as taskCreateService.js and for the same reason: the endpoint is
// known here and nowhere above. The two files stay separate because API 06
// and API 07 are separate cards, even though they share a URL.

import { TaskRequestError } from './taskCreateService';

const BASE_URL = import.meta.env.VITE_API_BASE_URL;

// The three filters the API accepts. Anything else in the object handed to
// getTasks is dropped rather than sent, so a typo in a caller cannot turn into
// a query string the API silently ignores.
const FILTER_NAMES = ['status_id', 'priority_id', 'assignee_id'];

/**
 * List the tasks of one project, newest first.
 *
 * Filters are optional. An unset or empty filter is left out of the query
 * string entirely, because `?status_id=` is not the same request as sending
 * no filter at all: the API would try to read it as an integer and answer 400.
 */
export async function getTasks(projectId, filters = {}) {
  const query = buildQuery(filters);
  const url = `${BASE_URL}/projects/${projectId}/tasks${query}`;

  let response;

  try {
    response = await fetch(url, {
      method: 'GET',
      // Membership of the project is what this endpoint checks, and it reads
      // the member from the session cookie.
      credentials: 'include',
      headers: { Accept: 'application/json' }
    });
  } catch {
    throw new TaskRequestError('Cannot reach the server.', 0);
  }

  const body = await parseBody(response);

  if (response.ok) {
    return body;
  }

  if (response.status === 403) {
    throw new TaskRequestError(detail(body, 'You are not signed in.'), 403);
  }

  if (response.status === 404) {
    // The API answers 404 both for a project that does not exist and for one
    // the caller cannot see, on purpose: a 403 would confirm it exists. The
    // wording here keeps that distinction hidden too.
    throw new TaskRequestError(detail(body, 'That project was not found.'), 404);
  }

  throw new TaskRequestError(detail(body, 'The tasks could not be loaded.'), response.status);
}

function buildQuery(filters) {
  const params = new URLSearchParams();

  FILTER_NAMES.forEach((name) => {
    const value = filters[name];

    if (value !== undefined && value !== null && value !== '') {
      params.append(name, value);
    }
  });

  const query = params.toString();

  return query ? `?${query}` : '';
}

async function parseBody(response) {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

function detail(body, fallback) {
  return (body && body.detail) || fallback;
}
