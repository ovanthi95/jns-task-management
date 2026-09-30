// API 09 service - POST /api/tasks/:taskId/comments
// Owner: Ovanthi

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

function csrfToken() {
  const cookie = document.cookie
    .split('; ')
    .find((part) => part.startsWith('csrftoken='));

  return cookie
    ? decodeURIComponent(cookie.slice('csrftoken='.length))
    : '';
}

export async function getComments(taskId) {
  const response = await fetch(
    `${API_BASE_URL}/tasks/${taskId}/comments`,
    {
      method: 'GET',
      credentials: 'include'
    }
  );

  const data = await response.json().catch(() => ([]));

  if (!response.ok) {
    throw new Error(data.detail || 'Unable to load comments.');
  }

  return data;
}

export async function createComment(taskId, commentText) {
  const response = await fetch(
    `${API_BASE_URL}/tasks/${taskId}/comments`,
    {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken()
      },
      body: JSON.stringify({ comment_text: commentText })
    }
  );

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const error = new Error(
      data.detail ||
      data.comment_text?.[0] ||
      'Unable to add comment.'
    );
    error.status = response.status;
    throw error;
  }

  return data;
}
