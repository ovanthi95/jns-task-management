// API 08 service - PATCH /api/tasks/:taskId
// Owner: Ovanthi

import { TaskRequestError } from './taskCreateService';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

export async function updateTask(taskId, changes) {
  let response;

  try {
    response = await fetch(`${BASE_URL}/tasks/${taskId}`, {
      method: 'PATCH',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...csrfHeader()
      },
      body: JSON.stringify(changes)
    });
  } catch {
    throw new TaskRequestError('Cannot reach the server.', 0);
  }

  const body = await parseBody(response);

  if (response.ok) return body;

  if (response.status === 400) {
    throw new TaskRequestError(
      'Please correct the fields below.',
      400,
      body && !body.detail ? body : {}
    );
  }

  if (response.status === 401) {
    throw new TaskRequestError(detail(body, 'Not authenticated.'), 401);
  }

  if (response.status === 403) {
    throw new TaskRequestError(
      detail(body, 'You do not have permission for this task change.'),
      403
    );
  }

  if (response.status === 404) {
    throw new TaskRequestError(detail(body, 'That task was not found.'), 404);
  }

  throw new TaskRequestError(
    detail(body, 'The task could not be updated.'),
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
  return (body && body.detail) || fallback;
}
