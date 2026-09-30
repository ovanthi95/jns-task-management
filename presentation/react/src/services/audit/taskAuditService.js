// API 11 service - GET /api/tasks/:taskId/audit
// Owner: Ovanthi

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

export async function getTaskAudit(taskId) {
  const response = await fetch(
    `${API_BASE_URL}/tasks/${taskId}/audit`,
    {
      method: 'GET',
      credentials: 'include'
    }
  );

  const data = await response.json().catch(() => ([]));

  if (!response.ok) {
    const error = new Error(
      data.detail || 'Unable to load task audit history.'
    );
    error.status = response.status;
    throw error;
  }

  return data;
}
