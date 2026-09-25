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
      // The hook already exposes the API error to the form.
    }
  };

  if (loading) {
    return (
      <MainCard title="Edit task">
        <Spinner animation="border" size="sm" /> Loading task...
      </MainCard>
    );
  }

  if (!task) {
    return (
      <MainCard title="Edit task">
        <Alert variant="danger">{error || 'Task not found.'}</Alert>
        <Link to={`/projects/${projectId}/tasks`}>Back to tasks</Link>
      </MainCard>
    );
  }

  const mayChangeAnything =
    permissions.canEditDetails
    || permissions.canReassign
    || permissions.canChangeAnyStatus
    || permissions.canCompleteAssigned;

  return (
    <MainCard title={`Edit task — ${task.title}`}>
      {!mayChangeAnything && (
        <Alert variant="warning">
          Your role does not allow changes to this task.
        </Alert>
      )}

      {permissions.canCompleteAssigned
        && !permissions.canChangeAnyStatus
        && (
          <Alert variant="info">
            As the assignee, you may only change the status to Completed.
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
            <Form.Label>Status ID</Form.Label>
            <Form.Control
              type="number"
              min={1}
              value={values.status_id}
              onChange={(event) => change('status_id', event.target.value)}
              disabled={
                !permissions.canChangeAnyStatus
                && !permissions.canCompleteAssigned
              }
              isInvalid={Boolean(fieldErrors.status_id)}
            />
            <Form.Control.Feedback type="invalid">
              {firstError(fieldErrors.status_id)}
            </Form.Control.Feedback>
          </Col>

          <Col xs={12}>
            <Form.Label>Description</Form.Label>
            <Form.Control
              as="textarea"
              rows={3}
              value={values.description}
              onChange={(event) => change('description', event.target.value)}
              disabled={!permissions.canEditDetails}
              isInvalid={Boolean(fieldErrors.description)}
            />
          </Col>

          <Col md={4}>
            <Form.Label>Task type ID</Form.Label>
            <Form.Control
              type="number"
              min={1}
              value={values.task_type_id}
              onChange={(event) => change('task_type_id', event.target.value)}
              disabled={!permissions.canEditDetails}
              isInvalid={Boolean(fieldErrors.task_type_id)}
            />
          </Col>

          <Col md={4}>
            <Form.Label>Priority ID</Form.Label>
            <Form.Control
              type="number"
              min={1}
              value={values.priority_id}
              onChange={(event) => change('priority_id', event.target.value)}
              disabled={!permissions.canEditDetails}
              isInvalid={Boolean(fieldErrors.priority_id)}
            />
          </Col>

          <Col md={4}>
            <Form.Label>Assignee ID</Form.Label>
            <Form.Control
              type="number"
              min={1}
              value={values.assignee_id}
              onChange={(event) => change('assignee_id', event.target.value)}
              disabled={!permissions.canReassign}
              isInvalid={Boolean(fieldErrors.assignee_id)}
            />
            <Form.Text>
              Reassignment is restricted to Admin in the JNS build.
            </Form.Text>
          </Col>

          <Col md={4}>
            <Form.Label>Start date</Form.Label>
            <Form.Control
              type="date"
              value={values.start_date}
              onChange={(event) => change('start_date', event.target.value)}
              disabled={!permissions.canEditDetails}
              isInvalid={Boolean(fieldErrors.start_date)}
            />
          </Col>

          <Col md={4}>
            <Form.Label>Due date</Form.Label>
            <Form.Control
              type="date"
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

            <Link
              to={`/projects/${projectId}/tasks`}
              className="btn btn-link ms-2"
            >
              Cancel
            </Link>
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
