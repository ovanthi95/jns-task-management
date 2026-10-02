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
    notifyAssignee,
    setNotifyAssignee,
    notice,
    change,
    save
  } = useTaskEdit(projectId, taskId);

  const submit = async (event) => {
    event.preventDefault();

    try {
      await save();
      if (!notice) {
        navigate(`/projects/${projectId}/tasks`);
      }
    } catch {
      // The hook exposes the API error to the form.
    }
  };

  if (loading) {
    return (
      <MainCard title="Edit task">
        <Spinner animation="border" size="sm" /> Loading task...
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
    permissions.canEditDetails
    || permissions.canReassign
    || permissions.canChangeAnyStatus
    || permissions.canCompleteAssigned;

  const activeUsers = options.users || [];
  const currentAssignee = task.assignees?.[0];
  const currentAssigneeIsActive = currentAssignee
    ? activeUsers.some(
        (item) => Number(item.user_id) === Number(currentAssignee.user_id)
      )
    : true;

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
      {notice && <Alert variant="warning">{notice}</Alert>}

      <Form onSubmit={submit}>
        <Row className="g-3">
          <Col md={8}>
            <Form.Label>Title</Form.Label>
            <Form.Control
              value={values.title}
              onChange={(event) => change('title', event.target.value)}
              disabled={!permissions.canEditDetails}
              isInvalid={Boolean(fieldErrors.title)}
              maxLength={200}
              required
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
                !permissions.canChangeAnyStatus
                && !permissions.canCompleteAssigned
              }
              isInvalid={Boolean(fieldErrors.status_id)}
            >
              {options.task_statuses.map((item) => (
                <option key={item.status_id} value={item.status_id}>
                  {item.status_name}
                </option>
              ))}
            </Form.Select>
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
            <Form.Control.Feedback type="invalid">
              {firstError(fieldErrors.description)}
            </Form.Control.Feedback>
          </Col>

          <Col md={4}>
            <Form.Label>Task type</Form.Label>
            <Form.Select
              value={values.task_type_id}
              onChange={(event) => change('task_type_id', event.target.value)}
              disabled={!permissions.canEditDetails}
              isInvalid={Boolean(fieldErrors.task_type_id)}
              required
            >
              <option value="">Choose type</option>
              {options.task_types.map((item) => (
                <option key={item.task_type_id} value={item.task_type_id}>
                  {item.type_name}
                </option>
              ))}
            </Form.Select>
            <Form.Control.Feedback type="invalid">
              {firstError(fieldErrors.task_type_id)}
            </Form.Control.Feedback>
          </Col>

          <Col md={4}>
            <Form.Label>Priority</Form.Label>
            <Form.Select
              value={values.priority_id}
              onChange={(event) => change('priority_id', event.target.value)}
              disabled={!permissions.canEditDetails}
              isInvalid={Boolean(fieldErrors.priority_id)}
              required
            >
              <option value="">Choose priority</option>
              {options.priorities.map((item) => (
                <option key={item.priority_id} value={item.priority_id}>
                  {item.priority_name}
                </option>
              ))}
            </Form.Select>
            <Form.Control.Feedback type="invalid">
              {firstError(fieldErrors.priority_id)}
            </Form.Control.Feedback>
          </Col>

          <Col md={4}>
            <Form.Label>Assignee</Form.Label>
            <Form.Select
              value={values.assignee_id}
              onChange={(event) => change('assignee_id', event.target.value)}
              disabled={!permissions.canReassign}
              isInvalid={Boolean(fieldErrors.assignee_id)}
              required
            >
              <option value="">Choose assignee</option>
              {currentAssignee && !currentAssigneeIsActive && (
                <option value={currentAssignee.user_id}>
                  {currentAssignee.first_name} {currentAssignee.last_name} — Current assignee
                </option>
              )}
              {activeUsers.map((item) => (
                <option key={item.user_id} value={item.user_id}>
                  {item.name}{item.role_name ? ` — ${item.role_name}` : ''}
                </option>
              ))}
            </Form.Select>
            <Form.Control.Feedback type="invalid">
              {firstError(fieldErrors.assignee_id)}
            </Form.Control.Feedback>
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
            <Form.Control.Feedback type="invalid">
              {firstError(fieldErrors.estimated_hours)}
            </Form.Control.Feedback>
          </Col>

          {permissions.canNotify && (
            <Col xs={12}>
              <Form.Check
                type="switch"
                id="notify-assignee-update"
                label="Email assignee about these changes"
                checked={notifyAssignee}
                onChange={(event) => setNotifyAssignee(event.target.checked)}
                disabled={saving}
              />
              <Form.Text>
                Sends the changes and updated task details to the selected assignee after saving.
              </Form.Text>
            </Col>
          )}

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
