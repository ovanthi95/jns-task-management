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
  other_task_type: '',
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
  const [notifyAssignee, setNotifyAssignee] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [fieldErrors, setFieldErrors] = useState({});
  const [notice, setNotice] = useState('');

  useEffect(() => {
    let active = true;

    async function load() {
      if (!projectId || !taskId) return;

      setLoading(true);
      setError('');

      try {
        const [tasks, taskOptions, sessionUser] = await Promise.all([
          getTasks(projectId),
          getTaskOptions(projectId),
          getSessionUser()
        ]);

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
      } catch (requestError) {
        if (active) setError(requestError.message);
      } finally {
        if (active) setLoading(false);
      }
    }

    load();

    return () => {
      active = false;
    };
  }, [projectId, taskId]);

  const permissions = useMemo(() => {
    const supplied = options?.current_user?.permissions;
    const role = String(user?.role_name || '').toLowerCase();
    const currentUserId = Number(user?.user_id);

    const isAssignee = (task?.assignees || []).some(
      (person) => Number(person.user_id) === currentUserId
    );

    const permissionSet = new Set(supplied || []);

    return {
      canEditDetails:
        permissionSet.has('edit_tasks')
        || role === 'admin'
        || role === 'manager',
      canReassign:
        permissionSet.has('reassign_tasks')
        || role === 'admin',
      canChangeAnyStatus:
        permissionSet.has('change_any_task_status')
        || role === 'admin'
        || role === 'manager',
      canCompleteAssigned:
        permissionSet.has('complete_assigned_tasks')
        || (!['admin', 'manager'].includes(role) && isAssignee),
      canNotify: permissionSet.has('send_task_notifications') || role === 'admin'
    };
  }, [options, task, user]);

  const change = (name, value) => {
    setValues((current) => ({ ...current, [name]: value }));
    setFieldErrors((current) => ({ ...current, [name]: undefined }));
    setNotice('');
  };

  const save = async () => {
    setSaving(true);
    setError('');
    setFieldErrors({});
    setNotice('');

    try {
      const changes = buildChanges(values, initialValues, permissions);

      if (Object.keys(changes).length === 0) {
        return task;
      }

      if (permissions.canNotify) {
        changes.notify_assignee = notifyAssignee;
      }

      const updated = await updateTask(taskId, changes);
      const loaded = toFormValues(updated);

      setTask(updated);
      setValues(loaded);
      setInitialValues(loaded);
      setNotifyAssignee(false);

      if (updated.email_warning) {
        setNotice(updated.email_warning);
      }

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
    user,
    options,
    values,
    loading,
    saving,
    error,
    fieldErrors,
    permissions,
    notifyAssignee,
    setNotifyAssignee,
    notice,
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
    other_task_type: task.other_task_type || '',
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
    copyText(changes, values, initial, 'title');
    copyText(changes, values, initial, 'description');
    copyNumber(changes, values, initial, 'task_type_id');
    copyText(changes, values, initial, 'other_task_type');
    copyNumber(changes, values, initial, 'priority_id');
    copyNullableText(changes, values, initial, 'start_date');
    copyNullableText(changes, values, initial, 'due_date');

    if (values.estimated_hours !== initial.estimated_hours) {
      changes.estimated_hours =
        values.estimated_hours === '' ? null : values.estimated_hours;
    }
  }

  if (
    permissions.canReassign
    && values.assignee_id !== initial.assignee_id
  ) {
    changes.assignee_id = Number(values.assignee_id);
  }

  if (
    (permissions.canChangeAnyStatus || permissions.canCompleteAssigned)
    && values.status_id !== initial.status_id
  ) {
    changes.status_id = Number(values.status_id);
  }

  return changes;
}

function copyText(target, values, initial, field) {
  if (values[field] !== initial[field]) {
    target[field] = values[field];
  }
}

function copyNumber(target, values, initial, field) {
  if (values[field] !== initial[field]) {
    target[field] = Number(values[field]);
  }
}

function copyNullableText(target, values, initial, field) {
  if (values[field] !== initial[field]) {
    target[field] = values[field] || null;
  }
}
