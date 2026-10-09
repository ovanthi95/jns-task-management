import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';

import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';

import MainCard from 'components/MainCard';
import { createTask } from 'services/tasks/taskCreateService';
import { uploadFile } from 'services/tasks/fileService';
import { getTaskOptions } from 'services/tasks/taskListService';

const MAX_FILE_SIZE = 10 * 1024 * 1024;

const empty = {
  title: '',
  description: '',
  task_type_id: '',
  other_task_type: '',
  priority_id: '',
  assignee_id: '',
  start_date: '',
  due_date: '',
  estimated_hours: ''
};

export default function TaskCreate() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [values, setValues] = useState(empty);
  const [options, setOptions] = useState(null);
  const [attachment, setAttachment] = useState(null);
  const [notifyAssignee, setNotifyAssignee] = useState(false);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;

    getTaskOptions(projectId)
      .then((data) => {
        if (active) setOptions(data);
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
  }, [projectId]);

  const change = (event) => {
    const { name, value } = event.target;

    setValues((current) => ({
      ...current,
      [name]: value,
      ...(name === 'task_type_id' && !isOtherTaskType(options, value)
        ? { other_task_type: '' }
        : {})
    }));
  };

  const chooseAttachment = (event) => {
    const file = event.target.files?.[0] || null;

    if (file && file.size > MAX_FILE_SIZE) {
      event.target.value = '';
      setAttachment(null);
      setError('Attachment must be 10 MB or smaller.');
      return;
    }

    setError('');
    setAttachment(file);
  };

  const submit = async (event) => {
    event.preventDefault();

    const newStatus = options?.task_statuses?.find(
      (item) => item.status_name === 'New'
    );

    if (!newStatus) {
      setError('The New task status is not configured.');
      return;
    }

    const isOther = isOtherTaskType(options, values.task_type_id);

    if (isOther && !values.other_task_type.trim()) {
      setError('Please specify the task type when Other is selected.');
      return;
    }

    setBusy(true);
    setError('');

    try {
      const result = await createTask(projectId, {
        title: values.title,
        description: values.description || null,
        task_type_id: Number(values.task_type_id),
        other_task_type: isOther ? values.other_task_type.trim() : null,
        status_id: Number(newStatus.status_id),
        priority_id: Number(values.priority_id),
        assignee_id: Number(values.assignee_id),
        start_date: values.start_date || null,
        due_date: values.due_date || null,
        estimated_hours: values.estimated_hours || null,
        notify_assignee: notifyAssignee
      });

      if (attachment) {
        try {
          await uploadFile(result.task_id, attachment);
        } catch (uploadError) {
          window.alert(
            `The task was created, but the attachment could not be uploaded: ${uploadError.message}`
          );
        }
      }

      if (result.email_warning) {
        window.alert(result.email_warning);
      }

      navigate(`/projects/${projectId}/tasks/${result.task_id}`);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  };

  if (loading) return <MainCard title="Add task">Loading...</MainCard>;

  if (!options?.can_create) {
    return (
      <MainCard title="Add task">
        <div className="alert alert-warning">
          You do not have permission to add tasks to this project.
        </div>
        <Link to={`/projects/${projectId}/tasks`}>Back to tasks</Link>
      </MainCard>
    );
  }

  const canNotify =
    options.current_user?.permissions?.includes('send_task_notifications');

  return (
    <MainCard title={`Add task — ${options.project.project_name}`}>
      <p className="text-muted">
        New tasks start with New status automatically.
      </p>

      <Form onSubmit={submit} className="col-lg-8">
        <Form.Group className="mb-3">
          <Form.Label>Task title</Form.Label>
          <Form.Control
            name="title"
            value={values.title}
            onChange={change}
            maxLength={200}
            required
          />
        </Form.Group>

        <Form.Group className="mb-3">
          <Form.Label>Description</Form.Label>
          <Form.Control
            as="textarea"
            rows={3}
            name="description"
            value={values.description}
            onChange={change}
          />
        </Form.Group>

        <div className="row">
          <Form.Group className="col-md-4 mb-3">
            <Form.Label>Task type</Form.Label>
            <Form.Select name="task_type_id" value={values.task_type_id} onChange={change} required>
              <option value="">Choose type</option>
              {options.task_types.map((item) => (
                <option key={item.task_type_id} value={item.task_type_id}>
                  {item.type_name}
                </option>
              ))}
            </Form.Select>
          </Form.Group>

          {isOtherTaskType(options, values.task_type_id) && (
            <Form.Group className="col-md-4 mb-3">
              <Form.Label>Specify task type</Form.Label>
              <Form.Control
                name="other_task_type"
                value={values.other_task_type}
                onChange={change}
                maxLength={100}
                required
                placeholder="e.g. Website maintenance"
              />
            </Form.Group>
          )}

          <Form.Group className="col-md-4 mb-3">
            <Form.Label>Priority</Form.Label>
            <Form.Select name="priority_id" value={values.priority_id} onChange={change} required>
              <option value="">Choose priority</option>
              {options.priorities.map((item) => (
                <option key={item.priority_id} value={item.priority_id}>
                  {item.priority_name}
                </option>
              ))}
            </Form.Select>
          </Form.Group>

          <Form.Group className="col-md-4 mb-3">
            <Form.Label>Assignee</Form.Label>
            <Form.Select name="assignee_id" value={values.assignee_id} onChange={change} required>
              <option value="">Choose assignee</option>
              {options.users.map((item) => (
                <option key={item.user_id} value={item.user_id}>
                  {item.name} — {item.role_name}
                </option>
              ))}
            </Form.Select>
          </Form.Group>
        </div>

        <div className="row">
          <Form.Group className="col-md-4 mb-3">
            <Form.Label>Start date</Form.Label>
            <Form.Control type="date" name="start_date" value={values.start_date} onChange={change} />
          </Form.Group>
          <Form.Group className="col-md-4 mb-3">
            <Form.Label>Due date</Form.Label>
            <Form.Control type="date" name="due_date" value={values.due_date} onChange={change} />
          </Form.Group>
          <Form.Group className="col-md-4 mb-3">
            <Form.Label>Estimated hours</Form.Label>
            <Form.Control
              type="number"
              min="0"
              step="0.25"
              name="estimated_hours"
              value={values.estimated_hours}
              onChange={change}
            />
          </Form.Group>
        </div>

        <Form.Group className="mb-3">
          <Form.Label>Attachment</Form.Label>
          <Form.Control
            type="file"
            onChange={chooseAttachment}
            accept=".pdf,.doc,.docx,.xls,.xlsx,.csv,.txt,.png,.jpg,.jpeg"
          />
          <Form.Text>Optional. Maximum 10 MB.</Form.Text>
        </Form.Group>

        {canNotify && (
          <Form.Check
            className="mb-3"
            type="switch"
            id="notify-assignee"
            checked={notifyAssignee}
            onChange={(event) => setNotifyAssignee(event.target.checked)}
            label="Email the assignee when this task is created"
          />
        )}

        {error && <div className="alert alert-danger">{error}</div>}

        <Button type="submit" disabled={busy}>
          {busy ? 'Adding task...' : 'Add task'}
        </Button>
        <Link to={`/projects/${projectId}/tasks`} className="btn btn-link ms-2">
          Cancel
        </Link>
      </Form>
    </MainCard>
  );
}

function isOtherTaskType(options, taskTypeId) {
  return options?.task_types?.some(
    (item) =>
      String(item.task_type_id) === String(taskTypeId)
      && item.type_name === 'Other'
  );
}
