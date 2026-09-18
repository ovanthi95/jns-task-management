import { useEffect, useState } from 'react';

// react-bootstrap
import Alert from 'react-bootstrap/Alert';
import Button from 'react-bootstrap/Button';
import Col from 'react-bootstrap/Col';
import Form from 'react-bootstrap/Form';
import Row from 'react-bootstrap/Row';
import Spinner from 'react-bootstrap/Spinner';
import Stack from 'react-bootstrap/Stack';

// project-imports
import MainCard from 'components/MainCard';
import { ApiError } from 'api/client';
import { createTask } from 'api/worklink';
import { useAuth } from 'contexts/AuthContext';
import { useTaskFormOptions } from 'hooks/useWorkLink';

// ==============================|| CREATE TASK ||============================== //

// POST /api/v1/projects/{project_id}/tasks  (service 11 in the API list).
//
// Field names match the serializer, not the database. organisation_id and
// created_by are deliberately NOT collected: the backend derives both from the
// authenticated user's JWT and rejects them in the body, so the browser can
// never assign a task to another organisation.
//
// Every dropdown below is filled from the API rather than from a constants
// file. Lookup ids are AUTO_INCREMENT values that differ between a seeded
// development database and RDS, so any hardcoded id is a bug waiting for
// deployment day.

const initialValues = {
  project_id: '',
  task_type_id: '',
  priority_id: '',
  status_id: '',
  title: '',
  description: '',
  start_date: '',
  due_date: '',
  estimated_hours: '',
  assignee_id: ''
};

// The API reports validation failures against serializer field names. The
// assignee control is singular in the UI but plural on the wire, so that one
// needs translating; the rest already line up.
const FIELD_ALIASES = { assignee_ids: 'assignee_id' };

export default function CreateTask() {
  const { canManage } = useAuth();
  const { projects, priorities, taskTypes, statuses, users, defaultStatusId, isLoading, error: optionsError } = useTaskFormOptions();

  const [values, setValues] = useState(initialValues);
  const [validated, setValidated] = useState(false);
  const [localErrors, setLocalErrors] = useState({});
  const [apiErrors, setApiErrors] = useState({});
  const [formError, setFormError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [created, setCreated] = useState(null);

  // Select the starting status as soon as the lookup arrives, and only if the
  // user has not already chosen one.
  useEffect(() => {
    if (defaultStatusId) {
      setValues((previous) => (previous.status_id ? previous : { ...previous, status_id: defaultStatusId }));
    }
  }, [defaultStatusId]);

  const handleChange = (event) => {
    const { name, value } = event.target;

    setValues((previous) => ({ ...previous, [name]: value }));
    setCreated(null);
    setFormError('');
    // Clear the server's complaint about this field: it was about the old
    // value, and leaving it visible while the user retypes is misleading.
    setApiErrors((previous) => {
      if (!(name in previous)) {
        return previous;
      }

      const next = { ...previous };

      delete next[name];
      return next;
    });
  };

  // Checks the browser cannot express with HTML attributes alone.
  const validateLocally = (current) => {
    const errors = {};

    if (current.start_date && current.due_date && current.due_date < current.start_date) {
      errors.due_date = 'Due date cannot be earlier than the start date.';
    }

    if (current.estimated_hours !== '') {
      const hours = Number(current.estimated_hours);

      if (Number.isNaN(hours) || hours < 0) {
        errors.estimated_hours = 'Estimated hours cannot be negative.';
      } else if (hours > 9999.99) {
        // estimated_hours is DECIMAL(6,2): 9999.99 is the largest value the
        // column can hold.
        errors.estimated_hours = 'Estimated hours cannot exceed 9999.99.';
      } else if (/\.\d{3,}$/.test(current.estimated_hours)) {
        // Two decimal places, or MySQL rounds silently and the stored value
        // disagrees with what the user typed.
        errors.estimated_hours = 'Use at most two decimal places.';
      }
    }

    return errors;
  };

  // Shape the form state into the JSON body the API expects. Empty optional
  // fields are sent as null rather than '' so they map onto nullable columns.
  const buildPayload = () => ({
    task_type_id: Number(values.task_type_id),
    priority_id: Number(values.priority_id),
    status_id: Number(values.status_id),
    title: values.title.trim(),
    description: values.description.trim() || null,
    start_date: values.start_date || null,
    due_date: values.due_date || null,
    estimated_hours: values.estimated_hours === '' ? null : Number(values.estimated_hours),
    // Assignees live in the task_assignees table, not on the task row, so this
    // is an array even though the form currently offers a single select. The
    // server creates the task and its assignee rows in one transaction.
    assignee_ids: values.assignee_id ? [Number(values.assignee_id)] : []
  });

  const handleSubmit = async (event) => {
    const form = event.currentTarget;

    event.preventDefault();
    event.stopPropagation();

    const errors = validateLocally(values);

    setLocalErrors(errors);
    setValidated(true);
    setApiErrors({});
    setFormError('');

    if (form.checkValidity() === false || Object.keys(errors).length > 0) {
      setCreated(null);
      return;
    }

    setSubmitting(true);

    try {
      const task = await createTask(values.project_id, buildPayload());

      setCreated(task);
      setValues({ ...initialValues, status_id: defaultStatusId });
      setValidated(false);
    } catch (error) {
      setCreated(null);

      if (error instanceof ApiError) {
        // 400 -- map each field error back onto the control that produced it.
        const mapped = {};

        Object.entries(error.fieldErrors).forEach(([field, message]) => {
          mapped[FIELD_ALIASES[field] ?? field] = message;
        });

        setApiErrors(mapped);

        if (error.status === 403) {
          setFormError('Your role does not allow creating tasks. Ask an Admin or Manager in your organisation.');
        } else if (error.status === 404) {
          // The API returns 404 rather than 403 for another tenant's project,
          // so this is also what a forged project_id looks like.
          setFormError('That project no longer exists, or it belongs to another organisation.');
        } else if (error.status === 409) {
          setFormError(error.message);
        } else {
          setFormError(error.message);
        }
      } else {
        setFormError(error?.message || 'Something went wrong while creating the task.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleReset = () => {
    setValues({ ...initialValues, status_id: defaultStatusId });
    setValidated(false);
    setLocalErrors({});
    setApiErrors({});
    setFormError('');
    setCreated(null);
  };

  // A server error outranks a client one for the same field: the server saw the
  // value that was actually submitted.
  const errorFor = (field) => apiErrors[field] || localErrors[field] || '';

  if (isLoading) {
    return (
      <MainCard title="Create Task">
        <Stack direction="horizontal" gap={2} className="align-items-center">
          <Spinner animation="border" size="sm" role="status" />
          <span className="text-muted">Loading projects, people and lookup values…</span>
        </Stack>
      </MainCard>
    );
  }

  if (optionsError) {
    return (
      <MainCard title="Create Task">
        <Alert variant="danger" className="mb-0">
          <Alert.Heading className="h6">The form could not be loaded</Alert.Heading>
          <p className="mb-0">{optionsError.message}</p>
        </Alert>
      </MainCard>
    );
  }

  const lookupsMissing = priorities.length === 0 || taskTypes.length === 0 || statuses.length === 0;

  return (
    <MainCard title="Create Task" subheader="Tasks are created against a project and stored in MySQL on Amazon RDS.">
      {!canManage && (
        <Alert variant="warning">
          You are signed in as a Member. The API allows only Admins and Managers to create tasks, so this form will return 403 on submit.
        </Alert>
      )}

      {lookupsMissing && (
        <Alert variant="warning">
          <Alert.Heading className="h6">Lookup tables are empty</Alert.Heading>
          <p className="mb-0">
            Priorities, task types or statuses returned no rows. Run <code>python manage.py seed_lookups</code> against the database the API
            is pointed at.
          </p>
        </Alert>
      )}

      {projects.length === 0 && (
        <Alert variant="info">
          There are no projects in your organisation yet. A task cannot exist without one, so create a project first.
        </Alert>
      )}

      {formError && (
        <Alert variant="danger" onClose={() => setFormError('')} dismissible>
          {formError}
        </Alert>
      )}

      <Form noValidate validated={validated} onSubmit={handleSubmit}>
        <Row>
          <Form.Group as={Col} md="6" className="mb-3" controlId="task-title">
            <Form.Label>Task Title</Form.Label>
            <Form.Control
              required
              type="text"
              name="title"
              value={values.title}
              onChange={handleChange}
              maxLength={200}
              placeholder="Enter task title"
              isInvalid={Boolean(errorFor('title'))}
            />
            <Form.Control.Feedback type="invalid">{errorFor('title') || 'Please enter a task title.'}</Form.Control.Feedback>
          </Form.Group>

          <Form.Group as={Col} md="6" className="mb-3" controlId="task-project">
            <Form.Label>Project</Form.Label>
            <Form.Select
              required
              name="project_id"
              value={values.project_id}
              onChange={handleChange}
              isInvalid={Boolean(errorFor('project_id'))}
            >
              <option value="" disabled>
                Select project
              </option>
              {projects.map((project) => (
                <option key={project.project_id} value={project.project_id}>
                  {project.project_name}
                </option>
              ))}
            </Form.Select>
            <Form.Control.Feedback type="invalid">{errorFor('project_id') || 'Please select a project.'}</Form.Control.Feedback>
          </Form.Group>
        </Row>

        <Form.Group className="mb-3" controlId="task-description">
          <Form.Label>Description</Form.Label>
          <Form.Control
            as="textarea"
            rows={4}
            name="description"
            value={values.description}
            onChange={handleChange}
            placeholder="Enter task description"
            isInvalid={Boolean(errorFor('description'))}
          />
          <Form.Control.Feedback type="invalid">{errorFor('description')}</Form.Control.Feedback>
        </Form.Group>

        <Row>
          <Form.Group as={Col} md="4" className="mb-3" controlId="task-type">
            <Form.Label>Task Type</Form.Label>
            <Form.Select
              required
              name="task_type_id"
              value={values.task_type_id}
              onChange={handleChange}
              isInvalid={Boolean(errorFor('task_type_id'))}
            >
              <option value="" disabled>
                Select task type
              </option>
              {taskTypes.map((taskType) => (
                <option key={taskType.task_type_id} value={taskType.task_type_id}>
                  {taskType.task_type_name}
                </option>
              ))}
            </Form.Select>
            <Form.Control.Feedback type="invalid">{errorFor('task_type_id') || 'Please select a task type.'}</Form.Control.Feedback>
          </Form.Group>

          <Form.Group as={Col} md="4" className="mb-3" controlId="task-priority">
            <Form.Label>Priority</Form.Label>
            <Form.Select
              required
              name="priority_id"
              value={values.priority_id}
              onChange={handleChange}
              isInvalid={Boolean(errorFor('priority_id'))}
            >
              <option value="" disabled>
                Select priority
              </option>
              {priorities.map((priority) => (
                <option key={priority.priority_id} value={priority.priority_id}>
                  {priority.priority_name}
                </option>
              ))}
            </Form.Select>
            <Form.Control.Feedback type="invalid">{errorFor('priority_id') || 'Please select a priority.'}</Form.Control.Feedback>
          </Form.Group>

          <Form.Group as={Col} md="4" className="mb-3" controlId="task-status">
            <Form.Label>Status</Form.Label>
            <Form.Select
              required
              name="status_id"
              value={values.status_id}
              onChange={handleChange}
              isInvalid={Boolean(errorFor('status_id'))}
            >
              <option value="" disabled>
                Select status
              </option>
              {statuses.map((status) => (
                <option key={status.status_id} value={status.status_id}>
                  {status.status_name}
                </option>
              ))}
            </Form.Select>
            <Form.Control.Feedback type="invalid">{errorFor('status_id') || 'Please select a status.'}</Form.Control.Feedback>
          </Form.Group>
        </Row>

        <Row>
          <Form.Group as={Col} md="4" className="mb-3" controlId="task-assignee">
            <Form.Label>Assignee</Form.Label>
            <Form.Select name="assignee_id" value={values.assignee_id} onChange={handleChange} isInvalid={Boolean(errorFor('assignee_id'))}>
              <option value="">Unassigned</option>
              {users.map((user) => (
                <option key={user.user_id} value={user.user_id}>
                  {user.full_name} ({user.role_name})
                </option>
              ))}
            </Form.Select>
            <Form.Control.Feedback type="invalid">{errorFor('assignee_id')}</Form.Control.Feedback>
          </Form.Group>

          <Form.Group as={Col} md="4" className="mb-3" controlId="task-start-date">
            <Form.Label>
              Start Date <span className="text-muted">(optional)</span>
            </Form.Label>
            <Form.Control
              type="date"
              name="start_date"
              value={values.start_date}
              onChange={handleChange}
              isInvalid={Boolean(errorFor('start_date'))}
            />
            <Form.Control.Feedback type="invalid">{errorFor('start_date')}</Form.Control.Feedback>
          </Form.Group>

          <Form.Group as={Col} md="4" className="mb-3" controlId="task-due-date">
            <Form.Label>Due Date</Form.Label>
            <Form.Control
              required
              type="date"
              name="due_date"
              value={values.due_date}
              onChange={handleChange}
              isInvalid={Boolean(errorFor('due_date'))}
            />
            <Form.Control.Feedback type="invalid">{errorFor('due_date') || 'Please select a due date.'}</Form.Control.Feedback>
          </Form.Group>
        </Row>

        <Form.Group className="mb-4" controlId="task-estimated-hours">
          <Form.Label>
            Estimated Hours <span className="text-muted">(optional)</span>
          </Form.Label>
          <Form.Control
            type="number"
            name="estimated_hours"
            value={values.estimated_hours}
            onChange={handleChange}
            min="0"
            max="9999.99"
            step="0.25"
            placeholder="e.g. 4.5"
            isInvalid={Boolean(errorFor('estimated_hours'))}
          />
          <Form.Control.Feedback type="invalid">{errorFor('estimated_hours')}</Form.Control.Feedback>
        </Form.Group>

        <Stack direction="horizontal" gap={2}>
          <Button type="submit" disabled={submitting || projects.length === 0}>
            {submitting && <Spinner animation="border" size="sm" className="me-2" role="status" />}
            {submitting ? 'Creating…' : 'Create Task'}
          </Button>
          <Button type="button" variant="light" onClick={handleReset} disabled={submitting}>
            Reset
          </Button>
        </Stack>
      </Form>

      {created && (
        <Alert variant="success" className="mt-4 mb-0" onClose={() => setCreated(null)} dismissible>
          <Alert.Heading className="h6">Task #{created.task_id} created</Alert.Heading>
          <p className="mb-0">
            <strong>{created.title}</strong> was added to {created.project_name} with status {created.status_name} and priority{' '}
            {created.priority_name}
            {created.assignees?.length ? `, assigned to ${created.assignees.map((row) => row.user.full_name).join(', ')}` : ', unassigned'}.
          </p>
        </Alert>
      )}
    </MainCard>
  );
}
