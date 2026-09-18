// ==============================|| WORKLINK ENDPOINTS ||============================== //

// One function per RESTful service, named after the operation rather than the
// URL, so a route change is a one-line edit here instead of a search across the
// views. The numbering matches the RESTful API List in the report and in
// worklink-api-contract.md.
//
// Nothing in this file sends organisation_id, created_by, assigned_by or
// uploaded_by. The API derives all four from the JWT and rejects them in the
// body. That is the tenant-isolation control, and the client must not look as
// though it participates in it.

import { apiFetch, unwrapList } from './client';

// ---------------------------------------------------------------- discovery

// 00 GET /  — self-describing index. Public, so a marker can list the services
// without a token.
export function getApiIndex() {
  return apiFetch('/', { auth: false });
}

// 00b GET /health — reports whether Django can reach MySQL.
export function getHealth() {
  return apiFetch('/health', { auth: false });
}

// ---------------------------------------------------------------- auth

// 01 POST /auth/register — creates the organisation and its first Admin.
export function register({ organisationName, organisationType, firstName, lastName, email, password }) {
  return apiFetch('/auth/register', {
    method: 'POST',
    auth: false,
    body: {
      organisation_name: organisationName,
      organisation_type: organisationType,
      first_name: firstName,
      last_name: lastName,
      email,
      password
    }
  });
}

// 02 POST /auth/login. `organisationId` is optional and only needed when the
// same address exists in two tenants — email is UNIQUE (organisation_id,
// email), not globally, so that is a legitimate state rather than an error.
export function login({ email, password, organisationId }) {
  return apiFetch('/auth/login', {
    method: 'POST',
    auth: false,
    body: {
      email,
      password,
      ...(organisationId ? { organisation_id: Number(organisationId) } : {})
    }
  });
}

// 03 GET /auth/me — the token's own user. Used on boot to decide whether a
// stored token is still good.
export function getMe(signal) {
  return apiFetch('/auth/me', { signal });
}

// ---------------------------------------------------------------- lookups

// 04, 05, 06 — global lookup tables, seeded by `manage.py seed_lookups`.
// pagination_class is None on all three, so these return bare arrays.

export async function getPriorities(signal) {
  return unwrapList(await apiFetch('/priorities', { signal }));
}

export async function getTaskTypes(signal) {
  return unwrapList(await apiFetch('/task-types', { signal }));
}

export async function getTaskStatuses(signal) {
  return unwrapList(await apiFetch('/task-statuses', { signal }));
}

export async function getRoles(signal) {
  return unwrapList(await apiFetch('/roles', { signal }));
}

// ---------------------------------------------------------------- directory

// 07 GET /users — colleagues in the caller's organisation, for the assignee
// picker. page_size is raised to the API's maximum so a small organisation
// fits in one request; anything larger needs a searchable control, not a
// bigger page.
export async function getOrganisationUsers(signal) {
  return unwrapList(await apiFetch('/users', { params: { page_size: 100 }, signal }));
}

// 07b POST /users — Admin only (403 otherwise).
export function inviteUser({ firstName, lastName, email, password, roleId, availability }) {
  return apiFetch('/users', {
    method: 'POST',
    body: {
      first_name: firstName,
      last_name: lastName,
      email,
      password,
      role_id: Number(roleId),
      ...(availability ? { availability } : {})
    }
  });
}

// ---------------------------------------------------------------- projects

// 08 GET /projects
export async function getProjects(signal) {
  return unwrapList(await apiFetch('/projects', { params: { page_size: 100 }, signal }));
}

// 09 POST /projects — Manager or Admin only.
export function createProject({ projectName, description, startDate, endDate, status }) {
  return apiFetch('/projects', {
    method: 'POST',
    body: {
      project_name: projectName,
      description: description || null,
      start_date: startDate || null,
      end_date: endDate || null,
      ...(status ? { status } : {})
    }
  });
}

// ---------------------------------------------------------------- tasks

// 10 GET /projects/{id}/tasks. `filters` accepts status_id, priority_id,
// assignee_id, q, page and page_size; empty values are stripped by the client.
export async function getProjectTasks(projectId, filters = {}, signal) {
  return unwrapList(await apiFetch(`/projects/${projectId}/tasks`, { params: filters, signal }));
}

/**
 * 11 POST /projects/{id}/tasks — create a task and staff it in one request.
 *
 * The server wraps both inserts in a transaction, so this either returns a
 * fully assigned task or changes nothing. `assignee_ids` is an array because
 * assignment lives in task_assignees, which allows many users per task.
 */
export function createTask(projectId, payload) {
  return apiFetch(`/projects/${projectId}/tasks`, { method: 'POST', body: payload });
}

// 12 GET /tasks/{id}
export function getTask(taskId, signal) {
  return apiFetch(`/tasks/${taskId}`, { signal });
}

// 13 PATCH /tasks/{id} — partial by design; the server writes one task_history
// row per field that actually changed.
export function updateTask(taskId, changes) {
  return apiFetch(`/tasks/${taskId}`, { method: 'PATCH', body: changes });
}

// 14 POST /tasks/{id}/assignees
export function assignUser(taskId, userId, assignmentRole) {
  return apiFetch(`/tasks/${taskId}/assignees`, {
    method: 'POST',
    body: {
      user_id: Number(userId),
      ...(assignmentRole ? { assignment_role: assignmentRole } : {})
    }
  });
}

// 21 DELETE /tasks/{id}/assignees/{user_id}
export function unassignUser(taskId, userId) {
  return apiFetch(`/tasks/${taskId}/assignees/${userId}`, { method: 'DELETE' });
}

// 15 / 16 comments
export async function getTaskComments(taskId, signal) {
  return unwrapList(await apiFetch(`/tasks/${taskId}/comments`, { signal }));
}

export function addTaskComment(taskId, commentText) {
  return apiFetch(`/tasks/${taskId}/comments`, { method: 'POST', body: { comment_text: commentText } });
}

// 19 GET /tasks/{id}/history
export async function getTaskHistory(taskId, signal) {
  return unwrapList(await apiFetch(`/tasks/${taskId}/history`, { signal }));
}

// ---------------------------------------------------------------- attachments

// 17 / 18 — the browser never uploads through Django. The API returns a
// short-lived presigned S3 URL, the browser PUTs the bytes straight to S3, and
// then 17b confirms the row. Two round trips, but the application tier never
// touches the file and stays stateless.

export async function getTaskAttachments(taskId, signal) {
  return unwrapList(await apiFetch(`/tasks/${taskId}/attachments`, { signal }));
}

export function requestUploadUrl(taskId, file) {
  return apiFetch(`/tasks/${taskId}/attachments`, {
    method: 'POST',
    body: {
      file_name: file.name,
      file_type: file.type || 'application/octet-stream',
      file_size: file.size
    }
  });
}

export function confirmUpload(attachmentId) {
  return apiFetch(`/attachments/${attachmentId}/confirm`, { method: 'POST' });
}

/**
 * Upload a file to S3 using a presigned URL.
 *
 * Deliberately NOT routed through apiFetch: this request goes to
 * s3.amazonaws.com, not to our API, and must carry no Authorization header —
 * S3 rejects a request that is both presigned and bearer-authenticated. The
 * Content-Type must match the one the URL was signed with, or the signature
 * check fails.
 */
export async function putFileToS3(uploadUrl, file) {
  const response = await fetch(uploadUrl, {
    method: 'PUT',
    headers: { 'Content-Type': file.type || 'application/octet-stream' },
    body: file
  });

  if (!response.ok) {
    throw new Error(`S3 rejected the upload (${response.status}). The presigned URL may have expired.`);
  }

  return true;
}
