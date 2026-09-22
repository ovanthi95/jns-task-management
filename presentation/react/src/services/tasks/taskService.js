/**
 * Service layer for the tasks pages.
 *
 * Every call here returns a promise and resolves with the same shape the real
 * endpoints return, so the views and the logic hooks never learn whether the
 * data came from a fixture or from HTTP. When Ovanthi's shared API client
 * lands, the bodies marked SWAP SEAM below are the only lines that change.
 *
 * Endpoints mirrored:
 *   API 06  POST /api/projects/:projectId/tasks
 *   API 07  GET  /api/projects/:projectId/tasks?status_id=&priority_id=&assignee_id=
 *
 * There is deliberately no fetch/axios client in this file. The backend uses
 * Django session authentication, and the shared frontend API/auth piece is
 * Ovanthi's. Inventing a second one here would be the competing pattern she
 * asked the team not to create.
 */

import { TASK_TYPES, TASK_STATUSES, PRIORITIES, PROJECTS, PROJECT_MEMBERS, TASKS, CURRENT_USER_ID } from './taskMockData';

// Fixtures are module-level constants, so anything that "creates" a task has to
// copy first. Without this a second visit to the list page would show rows the
// server never stored.
let createdTasks = [];
let nextTaskId = 9001;

// The delay is not decoration. It forces the views to handle a loading state
// now, rather than looking finished until the real endpoint is slower than a
// synchronous return.
const LATENCY_MS = 250;

function settle(value) {
  return new Promise((resolve) => setTimeout(() => resolve(value), LATENCY_MS));
}

/**
 * Rejects with the same shape DRF sends, so error handling written against the
 * mock keeps working against the endpoint:
 *
 *   { status: 400, data: { detail: '...' } }
 */
function reject(status, detail) {
  return new Promise((_, rejectPromise) => setTimeout(() => rejectPromise({ status, data: { detail } }), LATENCY_MS));
}

/**
 * API 07 treats a filter that is present but not a positive integer as a client
 * error, and a filter that is a valid id matching nothing as an empty result.
 * Returns the parsed integer, or null when the filter was not supplied.
 * Throws a plain Error the caller turns into a 400.
 */
function parseIdFilter(raw, fieldName) {
  if (raw === undefined || raw === null || raw === '') return null;

  const value = Number(raw);
  if (!Number.isInteger(value) || value < 1) {
    throw new Error(`${fieldName} must be a positive integer.`);
  }
  return value;
}

// ==============================|| LOOKUPS ||============================== //

/**
 * Task types, statuses and priorities are global lookups. No endpoint for them
 * exists on the agreed REST list yet, so these resolve from the fixture and
 * will need a real source before the dropdowns can be trusted.
 */
export function getLookups() {
  // SWAP SEAM - replace with the lookup endpoints once they are agreed.
  return settle({
    task_types: TASK_TYPES,
    statuses: TASK_STATUSES,
    priorities: PRIORITIES
  });
}

/**
 * Projects the signed-in user belongs to. API 05 (Jessie) owns this; the
 * project selector needs something to point at until it lands.
 */
export function listProjects() {
  // SWAP SEAM - API 05.
  return settle(PROJECTS);
}

/**
 * Members of one project. The assignee dropdown is per project rather than a
 * list of every user, because API 06 rejects an assignee who holds no
 * ProjectMember row for that project.
 */
export function listProjectMembers(projectId) {
  const id = Number(projectId);
  // SWAP SEAM - API 05 members endpoint.
  return settle(PROJECT_MEMBERS[id] ?? []);
}

// ==============================|| API 07 - LIST ||============================== //

/**
 * GET /api/projects/:projectId/tasks
 *
 * filters: { status_id, priority_id, assignee_id } - each optional.
 * Malformed filter -> rejects 400. Valid filter matching nothing -> [].
 */
export function listProjectTasks(projectId, filters = {}) {
  const id = Number(projectId);
  if (!Number.isInteger(id) || id < 1) {
    return reject(400, 'projectId must be a positive integer.');
  }

  let statusId;
  let priorityId;
  let assigneeId;
  try {
    statusId = parseIdFilter(filters.status_id, 'status_id');
    priorityId = parseIdFilter(filters.priority_id, 'priority_id');
    assigneeId = parseIdFilter(filters.assignee_id, 'assignee_id');
  } catch (err) {
    return reject(400, err.message);
  }

  // A project the user cannot reach is a 404, not an empty list, so an unknown
  // id here has to fail rather than quietly return nothing.
  if (!PROJECTS.some((project) => project.project_id === id)) {
    return reject(404, 'Not found.');
  }

  // SWAP SEAM - the block below is what the endpoint does server-side.
  let rows = [...TASKS, ...createdTasks].filter((task) => task.project_id === id);

  if (statusId !== null) rows = rows.filter((task) => task.status_id === statusId);
  if (priorityId !== null) rows = rows.filter((task) => task.priority_id === priorityId);
  if (assigneeId !== null) {
    rows = rows.filter((task) => task.assignees.some((assignee) => assignee.user_id === assigneeId));
  }

  return settle(rows);
}

// ==============================|| API 06 - CREATE ||============================== //

/**
 * POST /api/projects/:projectId/tasks
 *
 * payload: { task_type_id, status_id, priority_id, assignee_id, title,
 *            description, start_date, due_date, estimated_hours }
 *
 * project_id comes from the URL and created_by from the session, so neither is
 * ever read off the body - sending them would be ignored by the endpoint.
 * Resolves with the created task, shaped like an API 07 row.
 */
export function createTask(projectId, payload) {
  const id = Number(projectId);
  if (!Number.isInteger(id) || id < 1) {
    return reject(400, 'projectId must be a positive integer.');
  }
  if (!PROJECTS.some((project) => project.project_id === id)) {
    return reject(404, 'Not found.');
  }

  // Server-side validation is the real gate. This repeats only the checks the
  // endpoint is known to make, so the form cannot look valid here and fail
  // there. It is not a substitute for the form's own validation.
  const title = (payload.title ?? '').trim();
  if (!title) return reject(400, 'title is required.');
  if (title.length > 200) return reject(400, 'title must be 200 characters or fewer.');

  const taskTypeId = Number(payload.task_type_id);
  const statusId = Number(payload.status_id);
  const priorityId = Number(payload.priority_id);
  const assigneeId = Number(payload.assignee_id);

  if (!TASK_TYPES.some((row) => row.task_type_id === taskTypeId)) {
    return reject(400, 'task_type_id is not a valid task type.');
  }
  if (!TASK_STATUSES.some((row) => row.status_id === statusId)) {
    return reject(400, 'status_id is not a valid status.');
  }
  if (!PRIORITIES.some((row) => row.priority_id === priorityId)) {
    return reject(400, 'priority_id is not a valid priority.');
  }

  const members = PROJECT_MEMBERS[id] ?? [];
  const assignee = members.find((member) => member.user_id === assigneeId);
  if (!assignee) {
    return reject(400, 'assignee_id must be a member of this project.');
  }

  // due_date before start_date is rejected server-side. Both are optional, so
  // the comparison only runs when both are present.
  if (payload.start_date && payload.due_date && payload.due_date < payload.start_date) {
    return reject(400, 'due_date cannot be earlier than start_date.');
  }

  const now = new Date().toISOString().replace(/\.\d{3}Z$/, 'Z');

  // Decimals go out as strings and blanks as null, because that is what DRF
  // puts on the wire. Keeping it identical here means the list page cannot
  // render a freshly created row differently from a reloaded one.
  const estimatedHours =
    payload.estimated_hours === '' || payload.estimated_hours === undefined || payload.estimated_hours === null
      ? null
      : Number(payload.estimated_hours).toFixed(2);

  const created = {
    task_id: nextTaskId++,
    project_id: id,
    task_type_id: taskTypeId,
    task_type_name: TASK_TYPES.find((row) => row.task_type_id === taskTypeId).type_name,
    status_id: statusId,
    status_name: TASK_STATUSES.find((row) => row.status_id === statusId).status_name,
    priority_id: priorityId,
    priority_name: PRIORITIES.find((row) => row.priority_id === priorityId).priority_name,
    title,
    description: payload.description?.trim() ? payload.description.trim() : null,
    start_date: payload.start_date || null,
    due_date: payload.due_date || null,
    estimated_hours: estimatedHours,
    // Nothing has been logged against a task that was created a moment ago.
    actual_hours: null,
    assignees: [
      {
        user_id: assignee.user_id,
        first_name: assignee.first_name,
        last_name: assignee.last_name,
        assignment_role: null
      }
    ],
    created_by_id: CURRENT_USER_ID,
    created_at: now,
    updated_at: now
  };

  // SWAP SEAM - the push below stands in for the INSERT.
  createdTasks.push(created);

  return settle(created);
}

/**
 * Drops anything created during this browser session. Only useful while the
 * service is fixture-backed; delete it along with the fixtures.
 */
export function resetCreatedTasks() {
  createdTasks = [];
  nextTaskId = 9001;
}
