const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

async function parseResponse(response) {
  const data = await response.json();

  if (!response.ok) {
    const firstFieldError = Object.values(data).find(
      (value) => Array.isArray(value) && value.length
    );

    throw new Error(
      firstFieldError?.[0] ||
      data.detail ||
      'Unable to complete the password request.'
    );
  }

  return data;
}

export async function changePassword(currentPassword, newPassword, confirmPassword) {
  const response = await fetch(`${API_BASE_URL}/auth/change-password`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword,
      confirm_password: confirmPassword
    })
  });

  return parseResponse(response);
}

export async function requestPasswordReset(email) {
  const response = await fetch(`${API_BASE_URL}/auth/forgot-password`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ email })
  });

  return parseResponse(response);
}

export async function resetPassword(uid, token, newPassword, confirmPassword) {
  const response = await fetch(
    `${API_BASE_URL}/auth/reset-password/${encodeURIComponent(uid)}/${encodeURIComponent(token)}`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        new_password: newPassword,
        confirm_password: confirmPassword
      })
    }
  );

  return parseResponse(response);
}
