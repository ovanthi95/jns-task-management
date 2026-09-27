// API 08 UI - Update task
// Owner: Ovanthi

import { Link, useNavigate, useParams } from 'react-router-dom';

import Alert from 'react-bootstrap/Alert';
import Button from 'react-bootstrap/Button';
import Col from 'react-bootstrap/Col';
import Form from 'react-bootstrap/Form';
import Row from 'react-bootstrap/Row';
import Spinner from 'react-bootstrap/Spinner';

import MainCard from 'components/MainCard';
import { useTaskEdit } from 'logic/tasks/useTaskEdit';

export default function TaskEdit() {
  const { projectId, taskId } = useParams();
  const navigate = useNavigate();

  const {
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
  } = useTaskEdit(projectId, taskId);

  const submit = async (event) => {
    event.preventDefault();

    try {
      await save();
      navigate(`/projects/${projectId}/tasks`);
    } catch {
      // Errors are displayed by the hook.
    }
  };

  if (loading) {
    return (
      <MainCard title="Edit task">
        <Spinner animation="border" size="sm" className="me-2" />
        Loading task...
      </MainCard>
    );
  }

  if (!task || !options) {
    return (
      <MainCard title="Edit task">
        <Alert variant="danger">{error || 'Task not found.'}</Alert>
        <Link to={`/projects/${projectId}/tasks`}>Back to tasks</Link>
      </MainCard>
    );
  }

  const mayChangeAnything =
    permissions.canEditDetails ||
    permissions.canReassign ||
    permissions.canChangeAnyStatus ||
    permissions.canCompleteAssigned;

  const statusOptions = permissions.canChangeAnyStatus
    ? options.task_statuses
    : options.task_statuses.filter((item) => item.status_name === 'Completed');

  return (
    <MainCard title={`Edit task — ${task.title}`}>
      {!mayChangeAnything && (
        <Alert variant="warning">
          Your role does not allow changes to this task.
        </Alert>
      )}

      {permissions.canCompleteAssigned &&
        !permissions.canChangeAnyStatus && (
          <Alert variant="info">
            As the assignee, you may only change this task to Completed.
          </Alert>
        )}

      {error && <Alert variant="danger">{error}</Alert>}

      <Form onSubmit={submit}>
        <Row className="g-3">
          <Col md={8}>
            <Form.Label>Title</Form.Label>
            <Form.Control
              value={values.title}
              onChange={(event) => change('title', event.target.value)}
              disabled={!permissions.canEditDetails}
              isInvalid={Boolean(fieldErrors.title)}
            />
            <Form.Control.Feedback type="invalid">
              {firstError(fieldErrors.title)}
            </Form.Control.Feedback>
          </Col>

          <Col md={4}>
            <Form.Label>Status</Form.Label>
            <Form.Select
              value={values.status_id}
              onChange={(event) => change('status_id', event.target.value)}
              disabled={
                !permissions.canChangeAnyStatus &&
                !permissions.canCompleteAssigned
              }
              isInvalid={Boolean(fieldErrors.status_id)}
            >
              {!permissions.canChangeAnyStatus &&
                !permissions.canCompleteAssigned && (
                  <option value={values.status_id}>{task.status_name}</option>
                )}

              {permissions.canCompleteAssigned &&
                !permissions.canChangeAnyStatus &&
                task.status_name !== 'Completed' && (
                  <option value={values.status_id}>{task.status_name}</option>
                )}

              {statusOptions.map((item) => (
                <option key={item.status_id} value={String(item.status_id)}>
                  {item.status_name}
                </option>
              ))}
            </Form.Select>
          </Col>

          <Col xs={12}>
            <Form.Label>Description</Form.Label>
            <Form.Control
              as="textarea"
              rows={3}
              value={values.description}
              onChange={(event) => change('description', event.target.value)}
              disabled={!permissions.canEditDetails}
            />
          </Col>

          <Col md={4}>
            <Form.Label>Task type</Form.Label>
            <Form.Select
              value={values.task_type_id}
              onChange={(event) => change('task_type_id', event.target.value)}
              disabled={!permissions.canEditDetails}
            >
              {options.task_types.map((item) => (
                <option key={item.task_type_id} value={String(item.task_type_id)}>
                  {item.type_name}
                </option>
              ))}
            </Form.Select>
          </Col>

          <Col md={4}>
            <Form.Label>Priority</Form.Label>
            <Form.Select
              value={values.priority_id}
              onChange={(event) => change('priority_id', event.target.value)}
              disabled={!permissions.canEditDetails}
            >
              {options.priorities.map((item) => (
                <option key={item.priority_id} value={String(item.priority_id)}>
                  {item.priority_name}
                </option>
              ))}
            </Form.Select>
          </Col>

          <Col md={4}>
            <Form.Label>Assignee</Form.Label>
            <Form.Select
              value={values.assignee_id}
              onChange={(event) => change('assignee_id', event.target.value)}
              disabled={!permissions.canReassign}
            >
              {options.users.map((item) => (
                <option key={item.user_id} value={String(item.user_id)}>
                  {item.name}{item.role_name ? ` — ${item.role_name}` : ''}
                </option>
              ))}
            </Form.Select>
            <Form.Text>Only Admin can reassign a task.</Form.Text>
          </Col>

          <Col md={4}>
            <Form.Label>Start date</Form.Label>
            <Form.Control
              type="date"
              value={values.start_date}
              onChange={(event) => change('start_date', event.target.value)}
              disabled={!permissions.canEditDetails}
            />
          </Col>

          <Col md={4}>
            <Form.Label>Due date</Form.Label>
            <Form.Control
              type="date"
              min={values.start_date || undefined}
              value={values.due_date}
              onChange={(event) => change('due_date', event.target.value)}
              disabled={!permissions.canEditDetails}
              isInvalid={Boolean(fieldErrors.due_date)}
            />
            <Form.Control.Feedback type="invalid">
              {firstError(fieldErrors.due_date)}
            </Form.Control.Feedback>
          </Col>

          <Col md={4}>
            <Form.Label>Estimated hours</Form.Label>
            <Form.Control
              type="number"
              min={0}
              step="0.25"
              value={values.estimated_hours}
              onChange={(event) => change('estimated_hours', event.target.value)}
              disabled={!permissions.canEditDetails}
              isInvalid={Boolean(fieldErrors.estimated_hours)}
            />
          </Col>

          <Col xs={12}>
            <Button type="submit" disabled={saving || !mayChangeAnything}>
              {saving ? 'Saving...' : 'Save changes'}
            </Button>

            <Button
              as={Link}
              to={`/projects/${projectId}/tasks`}
              variant="light"
              className="ms-2"
              disabled={saving}
            >
              Cancel
            </Button>
          </Col>
        </Row>
      </Form>
    </MainCard>
  );
}

function firstError(value) {
  if (Array.isArray(value)) return value[0];
  return value || '';
}
