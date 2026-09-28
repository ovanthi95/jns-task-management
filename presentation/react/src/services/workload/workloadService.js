const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

export async function getWorkload() {
  const response = await fetch(`${API_BASE_URL}/workload`, {
    credentials: 'include'
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.detail || 'Unable to load workload.');
  }

  return data;
}

export async function getUserWorkloadTasks(userId) {
  const response = await fetch(
    `${API_BASE_URL}/workload/users/${userId}/tasks`,
    { credentials: 'include' }
  );

  const data = await response.json().catch(() => ([]));

  if (!response.ok) {
    throw new Error(data.detail || 'Unable to load user workload.');
  }

  return data;
}
