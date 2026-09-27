const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

export async function getHistory({
  entityType,
  search = '',
  changedBy = '',
  from = '',
  to = ''
}) {
  const params = new URLSearchParams({
    entity_type: entityType
  });

  if (search.trim()) params.set('search', search.trim());
  if (changedBy) params.set('changed_by', changedBy);
  if (from) params.set('from', from);
  if (to) params.set('to', to);

  const response = await fetch(
    `${API_BASE_URL}/history?${params.toString()}`,
    { credentials: 'include' }
  );

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.detail || 'Unable to load History.');
  }

  return data;
}
