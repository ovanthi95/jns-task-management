// API 10 service - POST /api/tasks/:taskId/files
// Owner: Manatka

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

function csrfToken() {
  const cookie = document.cookie
    .split('; ')
    .find((part) => part.startsWith('csrftoken='));

  return cookie
    ? decodeURIComponent(cookie.slice('csrftoken='.length))
    : '';
}

export async function getFiles(taskId) {
  const response = await fetch(
    `${API_BASE_URL}/tasks/${taskId}/files`,
    {
      method: 'GET',
      credentials: 'include'
    }
  );

  const data = await response.json().catch(() => ([]));

  if (!response.ok) {
    throw new Error(data.detail || 'Unable to load attachments.');
  }

  return data;
}

export async function uploadFile(taskId, file) {
  const form = new FormData();
  form.append('file', file);

  const response = await fetch(`${API_BASE_URL}/tasks/${taskId}/files`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'X-CSRFToken': csrfToken()
    },
    body: form
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const error = new Error(
      data.detail ||
      data.file?.[0] ||
      'Upload failed.'
    );
    error.status = response.status;
    error.fields = response.status === 400 && !data.detail ? data : {};
    throw error;
  }

  return data;
}
