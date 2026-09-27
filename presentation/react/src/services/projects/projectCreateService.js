// API 04 service - POST /api/projects
// Owner: Jesse

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

function csrfToken() {
  const cookie = document.cookie
    .split('; ')
    .find((part) => part.startsWith('csrftoken='));

  return cookie
    ? decodeURIComponent(cookie.slice('csrftoken='.length))
    : '';
}

export async function createProject(values) {
  const response = await fetch(`${API_BASE_URL}/projects`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken()
    },
    body: JSON.stringify(values)
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const error = new Error(
      data.detail ||
      Object.values(data).flat().join(' ') ||
      'Unable to create project.'
    );
    error.status = response.status;
    error.fields = response.status === 400 && !data.detail ? data : {};
    throw error;
  }

  return data;
}
