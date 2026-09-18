// ==============================|| WORKLINK DATA HOOKS ||============================== //

// SWR wrappers over the API functions. SWR is already a dependency of this
// template (it backs api/menu.js), so using it here adds no new package and
// gives request de-duplication for free: the assignee picker, the task board
// and the project page can all ask for /users and only one request is sent.

import useSWR from 'swr';

// project-imports
import * as api from 'api/worklink';
import { useAuth } from 'contexts/AuthContext';

// The four lookup tables change only when someone runs `seed_lookups`, so
// there is no value in revalidating them on every window focus. Projects and
// users do change during a session, so they get a shorter deduping window.
const LOOKUP_OPTIONS = {
  revalidateOnFocus: false,
  revalidateOnReconnect: false,
  dedupingInterval: 5 * 60 * 1000
};

const DIRECTORY_OPTIONS = {
  revalidateOnFocus: false,
  dedupingInterval: 30 * 1000
};

// Every one of these endpoints requires a token, so the SWR key is null until
// the user is signed in. A null key tells SWR not to fetch, which stops the
// app firing six guaranteed-401 requests on the login page.
function useAuthedSWR(key, fetcher, options) {
  const { isAuthenticated } = useAuth();

  return useSWR(isAuthenticated ? key : null, fetcher, options);
}

export function usePriorities() {
  return useAuthedSWR('worklink/priorities', () => api.getPriorities(), LOOKUP_OPTIONS);
}

export function useTaskTypes() {
  return useAuthedSWR('worklink/task-types', () => api.getTaskTypes(), LOOKUP_OPTIONS);
}

export function useTaskStatuses() {
  return useAuthedSWR('worklink/task-statuses', () => api.getTaskStatuses(), LOOKUP_OPTIONS);
}

export function useRoles() {
  return useAuthedSWR('worklink/roles', () => api.getRoles(), LOOKUP_OPTIONS);
}

export function useProjects() {
  return useAuthedSWR('worklink/projects', () => api.getProjects(), DIRECTORY_OPTIONS);
}

export function useOrganisationUsers() {
  return useAuthedSWR('worklink/users', () => api.getOrganisationUsers(), DIRECTORY_OPTIONS);
}

/**
 * Everything the Create Task form needs, in one hook.
 *
 * The five requests run in parallel because they are five independent SWR
 * hooks, not a chain — the form is usable as soon as the slowest returns.
 *
 * `defaultStatusId` is derived rather than hardcoded. The old mock file pinned
 * it to 1 on the assumption that 'New' is the first AUTO_INCREMENT id, which is
 * only true on a freshly seeded database. GET /task-statuses is ordered by
 * display_order, so the first row is the intended starting status whatever its
 * id turns out to be — the same rule the server applies in
 * tasks.serializers.default_status().
 */
export function useTaskFormOptions() {
  const projects = useProjects();
  const priorities = usePriorities();
  const taskTypes = useTaskTypes();
  const statuses = useTaskStatuses();
  const users = useOrganisationUsers();

  const parts = [projects, priorities, taskTypes, statuses, users];
  const statusList = statuses.data ?? [];

  return {
    projects: projects.data ?? [],
    priorities: priorities.data ?? [],
    taskTypes: taskTypes.data ?? [],
    statuses: statusList,
    users: users.data ?? [],
    defaultStatusId: statusList.length ? String(statusList[0].status_id) : '',
    isLoading: parts.some((part) => part.isLoading),
    // First failure wins; they all fail the same way (API unreachable, token
    // rejected) so showing five identical banners would help nobody.
    error: parts.map((part) => part.error).find(Boolean) ?? null
  };
}
