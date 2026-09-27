const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

function csrfToken() {
  const cookie = document.cookie
    .split('; ')
    .find((part) => part.startsWith('csrftoken='));

  return cookie
    ? decodeURIComponent(cookie.slice('csrftoken='.length))
    : '';
}

function errorMessage(data, fallback) {
  if (data.detail) return data.detail;

  const messages = Object.values(data)
    .flat()
    .filter(Boolean);

  return messages.length ? messages.join(' ') : fallback;
}

export async function getRoles() {
  const response = await fetch(`${API_BASE_URL}/roles`, {
    credentials: 'include'
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(errorMessage(data, 'Unable to load roles.'));
  }

  return data;
}

export async function createRole(values) {
  const response = await fetch(`${API_BASE_URL}/roles`, {
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
    throw new Error(errorMessage(data, 'Unable to create role.'));
  }

  return data;
}

export async function updateRole(roleId, values) {
  const response = await fetch(`${API_BASE_URL}/roles/${roleId}`, {
    method: 'PATCH',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken()
    },
    body: JSON.stringify(values)
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(errorMessage(data, 'Unable to update role.'));
  }

  return data;
}
