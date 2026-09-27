// API 08 UI logic
// Owner: Ovanthi

import { useEffect, useMemo, useState } from 'react';

import { getSessionUser } from 'services/auth/sessionService';
import { getTaskOptions, getTasks } from 'services/tasks/taskListService';
import { updateTask } from 'services/tasks/taskUpdateService';

const EMPTY = {
  title: '',
  description: '',
  task_type_id: '',
  priority_id: '',
  assignee_id: '',
  start_date: '',
  due_date: '',
  estimated_hours: '',
  status_id: ''
};

export function useTaskEdit(projectId, taskId) {
  const [task, setTask] = useState(null);
  const [user, setUser] = useState(null);
  const [options, setOptions] = useState(null);
  const [values, setValues] = useState(EMPTY);
  const [initialValues, setInitialValues] = useState(EMPTY);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [fieldErrors, setFieldErrors] = useState({});

  useEffect(() => {
    let active = true;

    Promise.all([
      getTasks(projectId),
      getTaskOptions(projectId),
      getSessionUser()
    ])
      .then(([tasks, taskOptions, sessionUser]) => {
        if (!active) return;

        const found = tasks.find(
          (item) => String(item.task_id) === String(taskId)
        );

        if (!found) {
          setError('Task not found.');
          return;
        }

        const loaded = toFormValues(found);

        setTask(found);
        setOptions(taskOptions);
        setUser(sessionUser);
        setValues(loaded);
        setInitialValues(loaded);
      })
      .catch((requestError) => {
        if (active) setError(requestError.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [projectId, taskId]);

  const permissions = useMemo(() => {
    const permissions = new Set(user?.permissions || []);
    const userId = Number(user?.user_id);
    const isAssignee = (task?.assignees || []).some(
      (person) => Number(person.user_id) === userId
    );

    return {
      canEditDetails: permissions.has('edit_tasks'),
      canReassign: permissions.has('reassign_tasks'),
      canChangeAnyStatus: permissions.has('change_any_task_status'),
      canCompleteAssigned:
        permissions.has('complete_assigned_tasks') && isAssignee
    };
  }, [task, user]);

  const change = (name, value) => {
    setValues((current) => ({ ...current, [name]: value }));
    setFieldErrors((current) => ({ ...current, [name]: undefined }));
  };

  const save = async () => {
    setSaving(true);
    setError('');
    setFieldErrors({});

    try {
      const changes = buildChanges(values, initialValues, permissions);

      if (Object.keys(changes).length === 0) {
        return task;
      }

      const updated = await updateTask(taskId, changes);
      const loaded = toFormValues(updated);

      setTask(updated);
      setValues(loaded);
      setInitialValues(loaded);

      return updated;
    } catch (requestError) {
      setError(requestError.message);
      setFieldErrors(requestError.fieldErrors || {});
      throw requestError;
    } finally {
      setSaving(false);
    }
  };

  return {
    task,
    options,
    values,
    loading,
    saving,
    error,
    fieldErrors,
    permissions,
    change,
    save
  };
}

function toFormValues(task) {
  const assignee = task.assignees?.[0];

  return {
    title: task.title || '',
    description: task.description || '',
    task_type_id: String(task.task_type_id || ''),
    priority_id: String(task.priority_id || ''),
    assignee_id: assignee ? String(assignee.user_id) : '',
    start_date: task.start_date || '',
    due_date: task.due_date || '',
    estimated_hours:
      task.estimated_hours === null || task.estimated_hours === undefined
        ? ''
        : String(task.estimated_hours),
    status_id: String(task.status_id || '')
  };
}

function buildChanges(values, initial, permissions) {
  const changes = {};

  if (permissions.canEditDetails) {
    copy(changes, values, initial, 'title');
    copy(changes, values, initial, 'description');
    copyNumber(changes, values, initial, 'task_type_id');
    copyNumber(changes, values, initial, 'priority_id');
    copyNullable(changes, values, initial, 'start_date');
    copyNullable(changes, values, initial, 'due_date');

    if (values.estimated_hours !== initial.estimated_hours) {
      changes.estimated_hours =
        values.estimated_hours === '' ? null : values.estimated_hours;
    }
  }

  if (
    permissions.canReassign &&
    values.assignee_id !== initial.assignee_id
  ) {
    changes.assignee_id = Number(values.assignee_id);
  }

  if (
    (permissions.canChangeAnyStatus || permissions.canCompleteAssigned) &&
    values.status_id !== initial.status_id
  ) {
    changes.status_id = Number(values.status_id);
  }

  return changes;
}

function copy(target, values, initial, field) {
  if (values[field] !== initial[field]) target[field] = values[field];
}

function copyNumber(target, values, initial, field) {
  if (values[field] !== initial[field]) target[field] = Number(values[field]);
}

function copyNullable(target, values, initial, field) {
  if (values[field] !== initial[field]) {
    target[field] = values[field] || null;
  }
}
