// API 06 UI - Create task
// Owner: Edward
//
// Markup only. Every decision about what happens on submit lives in
// useTaskCreate, and every decision about how the request is made lives in
// taskCreateService.
//
// The four lookups are number inputs rather than dropdowns. The agreed REST
// list has no service that returns task types, statuses, priorities or the
// members of a project, so there is nothing to populate a dropdown from, and
// adding such an endpoint would be work on a card nobody has been given. The
// ids are seeded by users/management/commands/seed_lookups.py and the demo
// uses those.

import PropTypes from 'prop-types';
import { useParams } from 'react-router-dom';

// react-bootstrap
import Alert from 'react-bootstrap/Alert';
import Button from 'react-bootstrap/Button';
import Col from 'react-bootstrap/Col';
import Form from 'react-bootstrap/Form';
import Row from 'react-bootstrap/Row';
import Spinner from 'react-bootstrap/Spinner';

// project-imports
import MainCard from 'components/MainCard';
import { useTaskCreate } from 'logic/tasks/useTaskCreate';

// ==============================|| TASKS - CREATE (API 06) ||============================== //

export default function TaskCreate({ projectId, onCreated }) {
  const params = useParams();

  // A prop when this form is embedded in the list page, the URL when it is
  // reached on its own. Both routes are registered, so both are supported.
  const project = projectId || params.projectId;

  const { form, fieldErrors, error, saving, created, setField, handleSubmit } = useTaskCreate(project, onCreated);

  return (
    <MainCard title="New task" subheader={`Project #${project}`}>
      <Form noValidate onSubmit={handleSubmit}>
        {error && <Alert variant="danger">{error}</Alert>}
        {created && <Alert variant="success">Task #{created.task_id} created.</Alert>}

        <Row className="g-3">
          <Col md={12}>
            <Field label="Title" name="title" errors={fieldErrors.title}>
              <Form.Control
                type="text"
                maxLength={200}
                value={form.title}
                isInvalid={Boolean(fieldErrors.title)}
                onChange={(event) => setField('title', event.target.value)}
              />
            </Field>
          </Col>

          <Col md={12}>
            <Field label="Description" name="description" errors={fieldErrors.description}>
              <Form.Control
                as="textarea"
                rows={3}
                value={form.description}
                isInvalid={Boolean(fieldErrors.description)}
                onChange={(event) => setField('description', event.target.value)}
              />
            </Field>
          </Col>

          <Col md={3}>
            <Field label="Task type id" name="task_type_id" errors={fieldErrors.task_type_id}>
              <Form.Control
                type="number"
                min={1}
                value={form.task_type_id}
                isInvalid={Boolean(fieldErrors.task_type_id)}
                onChange={(event) => setField('task_type_id', event.target.value)}
              />
            </Field>
          </Col>

          <Col md={3}>
            <Field label="Status id" name="status_id" errors={fieldErrors.status_id}>
              <Form.Control
                type="number"
                min={1}
                value={form.status_id}
                isInvalid={Boolean(fieldErrors.status_id)}
                onChange={(event) => setField('status_id', event.target.value)}
              />
            </Field>
          </Col>

          <Col md={3}>
            <Field label="Priority id" name="priority_id" errors={fieldErrors.priority_id}>
              <Form.Control
                type="number"
                min={1}
                value={form.priority_id}
                isInvalid={Boolean(fieldErrors.priority_id)}
                onChange={(event) => setField('priority_id', event.target.value)}
              />
            </Field>
          </Col>

          <Col md={3}>
            <Field label="Assignee user id" name="assignee_id" errors={fieldErrors.assignee_id} help="Must be a member of this project.">
              <Form.Control
                type="number"
                min={1}
                value={form.assignee_id}
                isInvalid={Boolean(fieldErrors.assignee_id)}
                onChange={(event) => setField('assignee_id', event.target.value)}
              />
            </Field>
          </Col>

          <Col md={4}>
            <Field label="Start date" name="start_date" errors={fieldErrors.start_date}>
              <Form.Control
                type="date"
                value={form.start_date}
                isInvalid={Boolean(fieldErrors.start_date)}
                onChange={(event) => setField('start_date', event.target.value)}
              />
            </Field>
          </Col>

          <Col md={4}>
            <Field label="Due date" name="due_date" errors={fieldErrors.due_date}>
              <Form.Control
                type="date"
                value={form.due_date}
                isInvalid={Boolean(fieldErrors.due_date)}
                onChange={(event) => setField('due_date', event.target.value)}
              />
            </Field>
          </Col>

          <Col md={4}>
            <Field label="Estimated hours" name="estimated_hours" errors={fieldErrors.estimated_hours}>
              <Form.Control
                type="number"
                min={0}
                step="0.25"
                value={form.estimated_hours}
                isInvalid={Boolean(fieldErrors.estimated_hours)}
                onChange={(event) => setField('estimated_hours', event.target.value)}
              />
            </Field>
          </Col>
        </Row>

        <div className="mt-4">
          <Button type="submit" disabled={saving}>
            {saving && <Spinner animation="border" size="sm" className="me-2" />}
            Create task
          </Button>
        </div>
      </Form>
    </MainCard>
  );
}

/**
 * One labelled control and whatever the API said about it.
 *
 * `errors` is the list DRF sent for this field, so a rule added to the
 * serializer shows up here without a change to this file.
 */
function Field({ label, name, errors, help, children }) {
  return (
    <Form.Group controlId={`task-${name}`}>
      <Form.Label>{label}</Form.Label>
      {children}
      {errors && <Form.Control.Feedback type="invalid">{[].concat(errors).join(' ')}</Form.Control.Feedback>}
      {help && !errors && <Form.Text className="text-muted">{help}</Form.Text>}
    </Form.Group>
  );
}

Field.propTypes = {
  label: PropTypes.string,
  name: PropTypes.string,
  errors: PropTypes.oneOfType([PropTypes.string, PropTypes.array]),
  help: PropTypes.string,
  children: PropTypes.node
};

TaskCreate.propTypes = {
  projectId: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  onCreated: PropTypes.func
};
