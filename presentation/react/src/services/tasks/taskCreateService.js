// API 06 service - POST /api/projects/:projectId/tasks
// Owner: Edward
//
// This is the only layer allowed to know the endpoint exists. The hook above
// it passes plain values and reads plain values back; it never sees a URL, a
// header or a status code.
//
// The request helper is written out here instead of being imported from a
// shared client because there is no shared client in the repo yet and adding
// one would be a file nobody owns. When somebody adds it, this function and
// its twin in taskListService.js collapse into it.

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

/**
 * The error the hooks catch.
 *
 * `fieldErrors` carries DRF's 400 body unchanged: an object keyed by field
 * name, each value a list of messages. The form reads it directly, so a new
 * rule added to the serializer shows up in the UI without a change here.
 */
export class TaskRequestError extends Error {
  constructor(message, status, fieldErrors) {
    super(message);
    this.name = 'TaskRequestError';
    this.status = status;
    this.fieldErrors = fieldErrors || {};
  }
}

/**
 * Create one task in one project and assign it to one person.
 *
 * `projectId` comes from the URL, never from the body. The API takes the
 * project from its own path and the author from the session, so sending
 * either here would be ignored at best.
 */
export async function createTask(projectId, task) {
  let response;

  try {
    response = await fetch(`${BASE_URL}/projects/${projectId}/tasks`, {
      method: 'POST',
      // The session cookie is what identifies the author server-side. Without
      // this the request is anonymous and comes back 403.
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...csrfHeader()
      },
      body: JSON.stringify(task)
    });
  } catch {
    // fetch only rejects when the request never completed. A 400 or a 500 is
    // a resolved promise, so this branch is the network being down.
    throw new TaskRequestError('Cannot reach the server.', 0);
  }

  return readResponse(response);
}

async function readResponse(response) {
  const body = await parseBody(response);

  if (response.ok) {
    return body;
  }

  if (response.status === 400) {
    throw new TaskRequestError('Please correct the fields below.', 400, body);
  }

  if (response.status === 403) {
    throw new TaskRequestError(detail(body, 'Your role is not permitted to create tasks.'), 403);
  }

  if (response.status === 404) {
    throw new TaskRequestError(detail(body, 'That project was not found.'), 404);
  }

  throw new TaskRequestError(detail(body, 'The task could not be created.'), response.status);
}

/**
 * The CSRF header Django's middleware looks for on an unsafe method.
 *
 * Django writes the value into a readable `csrftoken` cookie and then expects
 * it echoed back in a header, which a cross-site form cannot do. GET is exempt,
 * so only this file needs it.
 *
 * The cookie is set by whatever view starts the session, so until API 01 is
 * implemented there is nothing to read and this returns nothing. Sending no
 * header is the same as today's behaviour, so adding it now costs nothing and
 * means this file needs no change when login lands.
 */
function csrfHeader() {
  const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]*)/);

  return match ? { 'X-CSRFToken': decodeURIComponent(match[1]) } : {};
}

async function parseBody(response) {
  // A 500 can come back as an HTML error page, so the parse is guarded rather
  // than assumed. Returning null here lets the callers fall back to their own
  // wording instead of throwing a SyntaxError at the user.
  try {
    return await response.json();
  } catch {
    return null;
  }
}

function detail(body, fallback) {
  return (body && body.detail) || fallback;
}
