// API 06 UI - Create task
// Owner: Edward

import { useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import { Link, useParams } from 'react-router-dom';

import Alert from 'react-bootstrap/Alert';
import Button from 'react-bootstrap/Button';
import Col from 'react-bootstrap/Col';
import Form from 'react-bootstrap/Form';
import Row from 'react-bootstrap/Row';
import Spinner from 'react-bootstrap/Spinner';

import MainCard from 'components/MainCard';
import { useTaskCreate } from 'logic/tasks/useTaskCreate';
import { getTaskCreateOptions } from 'services/tasks/taskCreateService';

export default function TaskCreate({ projectId, onCreated }) {
  const params = useParams();
  const project = projectId || params.projectId;
  const [options, setOptions] = useState(null);
  const [optionsError, setOptionsError] = useState('');
  const [loadingOptions, setLoadingOptions] = useState(true);

  const {
    form,
    fieldErrors,
    error,
    saving,
    created,
    setField,
    handleSubmit
  } = useTaskCreate(project, onCreated);

  useEffect(() => {
    let active = true;

    getTaskCreateOptions(project)
      .then((data) => {
        if (!active) return;
        setOptions(data);

        if (data.new_status_id) {
          setField('status_id', String(data.new_status_id));
        }
      })
      .catch((err) => {
        if (active) setOptionsError(err.message);
      })
      .finally(() => {
        if (active) setLoadingOptions(false);
      });

    return () => {
      active = false;
    };
  }, [project]);

  if (loadingOptions) {
    return (
      <MainCard title="New task">
        <Spinner animation="border" size="sm" className="me-2" />
        Loading task options...
      </MainCard>
    );
  }

  if (optionsError) {
    return (
      <MainCard title="New task">
        <Alert variant="danger">{optionsError}</Alert>
      </MainCard>
    );
  }

  if (!options?.can_create) {
    return (
      <MainCard title="New task">
        <Alert variant="warning">
          Tasks can only be added to an Active project by an Admin or Manager.
        </Alert>
        <Button
          as={Link}
          to={`/projects/${project}/tasks`}
          variant="outline-secondary"
          size="sm"
        >
          Back to tasks
        </Button>
      </MainCard>
    );
  }

  return (
    <MainCard
      title={`New task — ${options.project?.project_name || `Project #${project}`}`}
      subheader={<p className="mb-0">New tasks start with New status automatically</p>}
    >
      <Form noValidate onSubmit={handleSubmit}>
        {error && <Alert variant="danger">{error}</Alert>}
        {created && (
          <Alert variant="success">
            Task #{created.task_id} created.
          </Alert>
        )}

        <Row className="g-3">
          <Col md={12}>
            <Field label="Title" name="title" errors={fieldErrors.title}>
              <Form.Control
                type="text"
                maxLength={200}
                required
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

          <Col md={4}>
            <Field label="Task type" name="task_type_id" errors={fieldErrors.task_type_id}>
              <Form.Select
                value={form.task_type_id}
                isInvalid={Boolean(fieldErrors.task_type_id)}
                onChange={(event) => setField('task_type_id', event.target.value)}
                required
              >
                <option value="">Choose type</option>
                {options.task_types.map((item) => (
                  <option key={item.task_type_id} value={item.task_type_id}>
                    {item.type_name}
                  </option>
                ))}
              </Form.Select>
            </Field>
          </Col>

          <Col md={4}>
            <Field label="Priority" name="priority_id" errors={fieldErrors.priority_id}>
              <Form.Select
                value={form.priority_id}
                isInvalid={Boolean(fieldErrors.priority_id)}
                onChange={(event) => setField('priority_id', event.target.value)}
                required
              >
                <option value="">Choose priority</option>
                {options.priorities.map((item) => (
                  <option key={item.priority_id} value={item.priority_id}>
                    {item.priority_name}
                  </option>
                ))}
              </Form.Select>
            </Field>
          </Col>

          <Col md={4}>
            <Field label="Assignee" name="assignee_id" errors={fieldErrors.assignee_id}>
              <Form.Select
                value={form.assignee_id}
                isInvalid={Boolean(fieldErrors.assignee_id)}
                onChange={(event) => setField('assignee_id', event.target.value)}
                required
              >
                <option value="">Choose assignee</option>
                {options.users.map((item) => (
                  <option key={item.user_id} value={item.user_id}>
                    {item.name}{item.role_name ? ` — ${item.role_name}` : ''}
                  </option>
                ))}
              </Form.Select>
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
                min={form.start_date || undefined}
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

        <div className="mt-4 d-flex gap-2">
          <Button type="submit" disabled={saving || !form.status_id}>
            {saving && <Spinner animation="border" size="sm" className="me-2" />}
            Create task
          </Button>
          <Button
            as={Link}
            to={`/projects/${project}/tasks`}
            variant="light"
            disabled={saving}
          >
            Cancel
          </Button>
        </div>
      </Form>
    </MainCard>
  );
}

function Field({ label, name, errors, help, children }) {
  return (
    <Form.Group controlId={`task-${name}`}>
      <Form.Label>{label}</Form.Label>
      {children}
      {errors && (
        <Form.Control.Feedback type="invalid">
          {[].concat(errors).join(' ')}
        </Form.Control.Feedback>
      )}
      {help && !errors && (
        <Form.Text className="text-muted">{help}</Form.Text>
      )}
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
