// API 10 service - POST /api/tasks/:taskId/files
// Owner: Manatka
//
// HTTP only. multipart/form-data with field name "file". No Content-Type
// header is set by hand: the browser adds the multipart boundary itself.
// Session cookie is sent with credentials: 'include'.

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

export async function uploadFile(taskId, file) {
  const form = new FormData();
  form.append('file', file);

  const response = await fetch(`${API_BASE_URL}/tasks/${taskId}/files`, {
    method: 'POST',
    credentials: 'include',
    body: form
  });

  const data = await response.json();

  if (!response.ok) {
    const error = new Error(data.detail || 'Upload failed.');
    error.status = response.status;
    error.fields = response.status === 400 && !data.detail ? data : {};
    throw error;
  }

  return data;
}