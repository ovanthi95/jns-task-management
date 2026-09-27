import { TaskRequestError } from './taskCreateService';

const BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

const FILTER_NAMES = ['status_id', 'priority_id', 'assignee_id'];

export async function getTasks(projectId, filters = {}) {
  const query = buildQuery(filters);
  const response = await fetch(
    `${BASE_URL}/projects/${projectId}/tasks${query}`,
    {
      method: 'GET',
      credentials: 'include',
      headers: { Accept: 'application/json' }
    }
  ).catch(() => {
    throw new TaskRequestError('Cannot reach the server.', 0);
  });

  const body = await parseBody(response);

  if (response.ok) return body || [];

  if (response.status === 401 || response.status === 403) {
    throw new TaskRequestError(
      detail(body, 'You are not signed in.'),
      response.status
    );
  }

  if (response.status === 404) {
    throw new TaskRequestError(
      detail(body, 'That project was not found.'),
      404
    );
  }

  throw new TaskRequestError(
    detail(body, 'The tasks could not be loaded.'),
    response.status
  );
}

export async function getTaskOptions(projectId) {
  const response = await fetch(
    `${BASE_URL}/projects/${projectId}/task-options`,
    {
      method: 'GET',
      credentials: 'include',
      headers: { Accept: 'application/json' }
    }
  ).catch(() => {
    throw new TaskRequestError('Cannot reach the server.', 0);
  });

  const body = await parseBody(response);

  if (response.ok) return body;

  throw new TaskRequestError(
    detail(body, 'Task options could not be loaded.'),
    response.status
  );
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
