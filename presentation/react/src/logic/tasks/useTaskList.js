// API 07 UI logic
// Owner: Edward
//
// Everything the task list page needs to behave, with no JSX and no fetch.
// The view renders what this returns; the service does the request.

import { useCallback, useEffect, useState } from 'react';

import { getTasks } from 'services/tasks/taskListService';

const EMPTY_FILTERS = {
  status_id: '',
  priority_id: '',
  assignee_id: ''
};

/**
 * Load and filter the tasks of one project.
 *
 * Filtering is done by the API, not in the browser, because the list is only
 * one page of a project's tasks and filtering what was already fetched would
 * quietly give a different answer than the same filter applied server-side.
 */
export function useTaskList(projectId) {
  const [tasks, setTasks] = useState([]);
  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(
    async (applied) => {
      // No project, no request. The page can be mounted before the id is
      // known, and asking for /projects/undefined/tasks is a guaranteed 404.
      if (!projectId) {
        return;
      }

      setLoading(true);
      setError('');

      try {
        setTasks(await getTasks(projectId, applied));
      } catch (requestError) {
        // The old rows are cleared on failure. Leaving them on screen under
        // an error message would show a list that no longer matches the
        // filters the user can see.
        setTasks([]);
        setError(requestError.message);
      } finally {
        setLoading(false);
      }
    },
    [projectId]
  );

  // First load, and again whenever the project changes. Filters are not in
  // the dependency list on purpose: typing in a filter field should not fire
  // a request per keystroke, so the reload is triggered by applyFilters.
  useEffect(() => {
    load(EMPTY_FILTERS);
  }, [load]);

  const setFilter = (name, value) => {
    setFilters((current) => ({ ...current, [name]: value }));
  };

  const applyFilters = (event) => {
    if (event) {
      event.preventDefault();
    }

    load(filters);
  };

  const clearFilters = () => {
    setFilters(EMPTY_FILTERS);
    load(EMPTY_FILTERS);
  };

  return {
    tasks,
    filters,
    loading,
    error,
    setFilter,
    applyFilters,
    clearFilters,
    reload: () => load(filters)
  };
}
