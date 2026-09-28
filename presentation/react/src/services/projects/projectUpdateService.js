import { csrfToken } from './projectCreateService';

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

export async function updateProject(projectId, changes) {
  const response = await fetch(
    `${API_BASE_URL}/projects/${projectId}`,
    {
      method: 'PATCH',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken()
      },
      body: JSON.stringify(changes)
    }
  );

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const error = new Error(
      data.detail ||
      Object.values(data).flat().join(' ') ||
      'Unable to update project.'
    );
    error.status = response.status;
    error.fields =
      response.status === 400 && !data.detail
        ? data
        : {};
    throw error;
  }

  return data;
}
