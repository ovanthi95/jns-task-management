/**
 * Create-form logic for API 06.
 *
 *   POST /api/projects/:projectId/tasks
 *
 * Holds the field values, the validation flag the react-bootstrap form reads,
 * and the submit state. The view renders inputs and hands back change events;
 * it does not call the service and does not build the request body.
 *
 * project_id comes from the URL and created_by from the session, so neither is
 * a field here. Putting them on the form would suggest the client can choose
 * them, and the endpoint ignores both if sent.
 */

import { useCallback, useEffect, useState } from 'react';

// project-imports
import { createTask, listProjectMembers, listProjects, getLookups } from 'services/tasks/taskService';

const EMPTY_FORM = {
  title: '',
  description: '',
  task_type_id: '',
  status_id: '',
  priority_id: '',
  assignee_id: '',
  start_date: '',
  due_date: '',
  estimated_hours: ''
};

export default function useTaskForm(projectId, { onCreated } = {}) {
  const [values, setValues] = useState(EMPTY_FORM);
  const [lookups, setLookups] = useState({ task_types: [], statuses: [], priorities: [] });
  const [members, setMembers] = useState([]);
  // Only so the page can name the project it is adding to. A form that does
  // not say where the task is going is easy to submit against the wrong one.
  const [project, setProject] = useState(null);

  // react-bootstrap only paints the green/red feedback once this is true, so
  // the form is not covered in red before the user has typed anything.
  const [validated, setValidated] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    getLookups()
      .then((rows) => {
        if (cancelled) return;
        setLookups(rows);
        // Status defaults to New. Every task starts there, and making the user
        // pick it is a field they will get wrong more often than right.
        setValues((current) => ({
          ...current,
          status_id: current.status_id || String(rows.statuses[0]?.status_id ?? '')
        }));
      })
      .catch(() => {
        if (!cancelled) setError('Could not load the task type, status and priority lists.');
      });

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!projectId) return undefined;
    let cancelled = false;

    listProjectMembers(projectId)
      .then((rows) => {
        if (!cancelled) setMembers(rows);
      })
      .catch(() => {
        if (!cancelled) setMembers([]);
      });

    listProjects()
      .then((rows) => {
        if (!cancelled) setProject(rows.find((row) => row.project_id === Number(projectId)) ?? null);
      })
      .catch(() => {
        if (!cancelled) setProject(null);
      });

    return () => {
      cancelled = true;
    };
  }, [projectId]);

  // An assignee chosen for one project is not a member of another, and API 06
  // rejects that. Clearing it on a project change stops the form submitting a
  // value the user can no longer see in the dropdown.
  useEffect(() => {
    setValues((current) => ({ ...current, assignee_id: '' }));
  }, [projectId]);

  const change = useCallback((name, value) => {
    setValues((current) => ({ ...current, [name]: value }));
    setError(null);
  }, []);

  const reset = useCallback(() => {
    setValues((current) => ({ ...EMPTY_FORM, status_id: current.status_id }));
    setValidated(false);
    setError(null);
  }, []);

  /**
   * Browser validation covers required and type per field. It cannot compare
   * two fields, so the date order is checked here and reported as a form-level
   * message. The endpoint checks it again; this only saves a round trip.
   */
  const dateOrderError =
    values.start_date && values.due_date && values.due_date < values.start_date ? 'Due date cannot be earlier than the start date.' : null;

  const submit = useCallback(
    (event) => {
      event.preventDefault();
      const form = event.currentTarget;

      setValidated(true);

      if (form.checkValidity() === false || dateOrderError) {
        event.stopPropagation();
        if (dateOrderError) setError(dateOrderError);
        return;
      }

      setSubmitting(true);
      setError(null);

      // Blank optional fields go as empty strings from the inputs. The service
      // turns those into null, which is what the column holds - sending '' to
      // a date column is an error, not an empty date.
      createTask(projectId, {
        title: values.title,
        description: values.description,
        task_type_id: values.task_type_id,
        status_id: values.status_id,
        priority_id: values.priority_id,
        assignee_id: values.assignee_id,
        start_date: values.start_date,
        due_date: values.due_date,
        estimated_hours: values.estimated_hours
      })
        .then((created) => {
          setSubmitting(false);
          reset();
          onCreated?.(created);
        })
        .catch((err) => {
          setSubmitting(false);
          setError(err?.data?.detail ?? 'Could not create the task. Please try again.');
        });
    },
    [projectId, values, dateOrderError, reset, onCreated]
  );

  return { values, change, lookups, members, project, validated, submitting, error, dateOrderError, submit, reset };
}
