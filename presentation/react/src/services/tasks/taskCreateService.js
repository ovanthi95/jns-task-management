// API 06 service - task creation

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

export class TaskRequestError extends Error {
  constructor(message, status, fieldErrors) {
    super(message);
    this.name = 'TaskRequestError';
    this.status = status;
    this.fieldErrors = fieldErrors || {};
  }
}

export async function getTaskCreateOptions(projectId) {
  let response;

  try {
    response = await fetch(`${BASE_URL}/projects/${projectId}/task-options`, {
      method: 'GET',
      credentials: 'include',
      headers: { Accept: 'application/json' }
    });
  } catch {
    throw new TaskRequestError('Cannot reach the server.', 0);
  }

  const body = await parseBody(response);

  if (!response.ok) {
    throw new TaskRequestError(
      detail(body, 'Unable to load task options.'),
      response.status
    );
  }

  return body;
}

export async function createTask(projectId, task) {
  let response;

  try {
    response = await fetch(`${BASE_URL}/projects/${projectId}/tasks`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...csrfHeader()
      },
      body: JSON.stringify(task)
    });
  } catch {
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
    throw new TaskRequestError(
      detail(body, 'Please correct the fields below.'),
      400,
      body && !body.detail ? body : {}
    );
  }

  if (response.status === 401) {
    throw new TaskRequestError(
      detail(body, 'Not authenticated.'),
      401
    );
  }

  if (response.status === 403) {
    throw new TaskRequestError(
      detail(body, 'Your role is not permitted to create tasks.'),
      403
    );
  }

  if (response.status === 404) {
    throw new TaskRequestError(
      detail(body, 'That project was not found.'),
      404
    );
  }

  throw new TaskRequestError(
    detail(body, 'The task could not be created.'),
    response.status
  );
}

function csrfHeader() {
  const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]*)/);
  return match ? { 'X-CSRFToken': decodeURIComponent(match[1]) } : {};
}

async function parseBody(response) {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

function detail(body, fallback) {
  if (!body) return fallback;
  if (typeof body.detail === 'string') return body.detail;
  if (Array.isArray(body.detail)) return body.detail.join(' ');
  return fallback;
}
