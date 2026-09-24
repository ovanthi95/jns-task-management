// API 06 UI logic
// Owner: Edward
//
// Form state, submission and error handling for the create page. No JSX, no
// fetch: the view renders what this returns and the service does the request.

import { useState } from 'react';

import { createTask } from 'services/tasks/taskCreateService';

// Every field starts as an empty string because that is what an <input>
// gives back. The conversion to the types the API wants happens once, in
// buildPayload, rather than being scattered through the form.
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

const REQUIRED_IDS = ['task_type_id', 'status_id', 'priority_id', 'assignee_id'];

/**
 * Drive the create-task form for one project.
 *
 * `onCreated` is called with the created task so the page that owns the list
 * can refresh without this hook knowing a list exists.
 */
export function useTaskCreate(projectId, onCreated) {
  const [form, setForm] = useState(EMPTY_FORM);
  const [fieldErrors, setFieldErrors] = useState({});
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [created, setCreated] = useState(null);

  const setField = (name, value) => {
    setForm((current) => ({ ...current, [name]: value }));

    // The message for this field goes as soon as it is touched. Leaving it
    // under a field the user is already fixing reads as a second error.
    setFieldErrors((current) => {
      if (!current[name]) {
        return current;
      }

      const next = { ...current };
      delete next[name];
      return next;
    });
  };

  const reset = () => {
    setForm(EMPTY_FORM);
    setFieldErrors({});
    setError('');
    setCreated(null);
  };

  const handleSubmit = async (event) => {
    if (event) {
      event.preventDefault();
    }

    setError('');
    setCreated(null);

    // A local check first, so the four required ids do not cost a round trip
    // to be told they are missing. The API checks them again regardless;
    // this is a convenience, not the rule.
    const missing = localErrors(form);

    if (Object.keys(missing).length > 0) {
      setFieldErrors(missing);
      return;
    }

    setFieldErrors({});
    setSaving(true);

    try {
      const task = await createTask(projectId, buildPayload(form));

      setCreated(task);
      setForm(EMPTY_FORM);

      if (onCreated) {
        onCreated(task);
      }
    } catch (requestError) {
      setError(requestError.message);
      setFieldErrors(requestError.fieldErrors || {});
    } finally {
      setSaving(false);
    }
  };

  return {
    form,
    fieldErrors,
    error,
    saving,
    created,
    setField,
    reset,
    handleSubmit
  };
}

function localErrors(form) {
  const errors = {};

  if (!form.title.trim()) {
    errors.title = ['Title cannot be blank.'];
  }

  REQUIRED_IDS.forEach((name) => {
    if (!form[name]) {
      errors[name] = ['This field is required.'];
    }
  });

  return errors;
}

/**
 * Turn the form's strings into the body the API expects.
 *
 * The optional fields are sent as null rather than as "", because the API
 * takes an empty string for a date as a malformed date and answers 400,
 * while null is an accepted absent value.
 */
function buildPayload(form) {
  return {
    title: form.title.trim(),
    description: form.description.trim() || null,
    task_type_id: Number(form.task_type_id),
    status_id: Number(form.status_id),
    priority_id: Number(form.priority_id),
    assignee_id: Number(form.assignee_id),
    start_date: form.start_date || null,
    due_date: form.due_date || null,
    estimated_hours: form.estimated_hours === '' ? null : form.estimated_hours
  };
}
