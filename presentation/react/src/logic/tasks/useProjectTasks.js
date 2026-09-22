/**
 * List-page logic for API 07.
 *
 * Holds the selected project, the three filters, the rows and the request
 * state. The view renders what this returns and calls back into it; it does
 * not talk to the service and does not filter anything itself.
 *
 *   GET /api/projects/:projectId/tasks?status_id=&priority_id=&assignee_id=
 *
 * Filtering is done server-side rather than over an in-memory array, because
 * that is what the endpoint does. Filtering locally would work against the
 * fixture and then quietly show the wrong page size once the list is paginated.
 */

import { useCallback, useEffect, useRef, useState } from 'react';

// project-imports
import { listProjectTasks, listProjects, listProjectMembers, getLookups } from 'services/tasks/taskService';

const NO_FILTERS = { status_id: '', priority_id: '', assignee_id: '' };

export default function useProjectTasks(initialProjectId) {
  const [projects, setProjects] = useState([]);
  const [projectId, setProjectId] = useState(initialProjectId ?? null);

  const [lookups, setLookups] = useState({ task_types: [], statuses: [], priorities: [] });
  const [members, setMembers] = useState([]);

  const [tasks, setTasks] = useState([]);
  const [filters, setFilters] = useState(NO_FILTERS);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Requests resolve out of order once there is a network involved. Only the
  // newest one is allowed to write to state, otherwise a slow response for a
  // filter the user has already changed lands on top of a fresh one.
  const requestRef = useRef(0);

  // Projects and lookups do not change while the page is open, so they are
  // fetched once rather than on every filter change.
  useEffect(() => {
    let cancelled = false;

    Promise.all([listProjects(), getLookups()])
      .then(([projectRows, lookupRows]) => {
        if (cancelled) return;
        setProjects(projectRows);
        setLookups(lookupRows);
        // Only default the selection when the caller did not pass one, so a
        // URL like /projects/2/tasks is not overwritten by the first project.
        setProjectId((current) => current ?? projectRows[0]?.project_id ?? null);
      })
      .catch((err) => {
        if (!cancelled) setError(messageFor(err));
      });

    return () => {
      cancelled = true;
    };
  }, []);

  // The assignee filter lists members of the selected project, because API 06
  // and API 07 both scope assignees to the project rather than the org.
  useEffect(() => {
    if (projectId === null) return undefined;
    let cancelled = false;

    listProjectMembers(projectId)
      .then((rows) => {
        if (!cancelled) setMembers(rows);
      })
      .catch(() => {
        if (!cancelled) setMembers([]);
      });

    return () => {
      cancelled = true;
    };
  }, [projectId]);

  const load = useCallback(() => {
    if (projectId === null) return;

    const requestId = ++requestRef.current;
    setLoading(true);
    setError(null);

    listProjectTasks(projectId, filters)
      .then((rows) => {
        if (requestRef.current !== requestId) return;
        setTasks(rows);
        setLoading(false);
      })
      .catch((err) => {
        if (requestRef.current !== requestId) return;
        // Rows are cleared on failure. Leaving the previous project's rows on
        // screen under a new project's heading would be worse than an empty
        // table with an error above it.
        setTasks([]);
        setError(messageFor(err));
        setLoading(false);
      });
  }, [projectId, filters]);

  useEffect(load, [load]);

  const changeProject = useCallback((nextProjectId) => {
    const value = Number(nextProjectId);
    setProjectId(Number.isInteger(value) && value > 0 ? value : null);
    // Filters are per project. A status id is global so it would survive the
    // switch, but an assignee id belongs to the old project's member list and
    // would return an empty table with no visible reason.
    setFilters(NO_FILTERS);
  }, []);

  const changeFilter = useCallback((name, value) => {
    setFilters((current) => ({ ...current, [name]: value }));
  }, []);

  const clearFilters = useCallback(() => setFilters(NO_FILTERS), []);

  const hasFilters = Object.values(filters).some((value) => value !== '');

  return {
    projects,
    projectId,
    changeProject,
    lookups,
    members,
    tasks,
    filters,
    hasFilters,
    changeFilter,
    clearFilters,
    loading,
    error,
    reload: load
  };
}

/**
 * Turns a rejected service call into something worth showing a user. The
 * service rejects with { status, data: { detail } }, matching DRF.
 */
function messageFor(err) {
  if (err?.status === 404) return 'That project does not exist, or you do not have access to it.';
  if (err?.data?.detail) return err.data.detail;
  return 'Could not load tasks. Please try again.';
}
