const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

function csrfToken() {
  const cookie = document.cookie
    .split('; ')
    .find((part) => part.startsWith('csrftoken='));
  return cookie ? decodeURIComponent(cookie.slice('csrftoken='.length)) : '';
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
    const message =
      data.detail
      || Object.values(data).flat().join(' ')
      || 'Unable to add project.';
    throw new Error(message);
  }

  return data.project || data;
}
