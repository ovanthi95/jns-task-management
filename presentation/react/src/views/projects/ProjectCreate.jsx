// API 04 UI - Create project
// Owner: Jesse

import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import Alert from 'react-bootstrap/Alert';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';

import MainCard from 'components/MainCard';
import { createProject } from 'services/projects/projectCreateService';

const empty = {
  project_name: '',
  description: '',
  start_date: '',
  end_date: ''
};

export default function ProjectCreate() {
  const navigate = useNavigate();
  const [values, setValues] = useState(empty);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const change = (event) => {
    setValues((current) => ({
      ...current,
      [event.target.name]: event.target.value
    }));
  };

  const submit = async (event) => {
    event.preventDefault();
    setBusy(true);
    setError('');

    try {
      await createProject({
        project_name: values.project_name.trim(),
        description: values.description.trim(),
        start_date: values.start_date || null,
        end_date: values.end_date || null
      });

      navigate('/projects');
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <MainCard
      title="Create project"
      subheader={<p className="mb-0">New projects start as Active</p>}
    >
      {error && <Alert variant="danger">{error}</Alert>}

      <Form onSubmit={submit} className="col-lg-8">
        <Form.Group className="mb-3" controlId="project_name">
          <Form.Label>Project name</Form.Label>
          <Form.Control
            name="project_name"
            value={values.project_name}
            onChange={change}
            maxLength={150}
            required
          />
        </Form.Group>

        <Form.Group className="mb-3" controlId="description">
          <Form.Label>Description</Form.Label>
          <Form.Control
            as="textarea"
            rows={4}
            name="description"
            value={values.description}
            onChange={change}
          />
        </Form.Group>

        <div className="row">
          <Form.Group className="col-md-6 mb-3" controlId="start_date">
            <Form.Label>Start date</Form.Label>
            <Form.Control
              type="date"
              name="start_date"
              value={values.start_date}
              onChange={change}
            />
          </Form.Group>

          <Form.Group className="col-md-6 mb-3" controlId="end_date">
            <Form.Label>End date</Form.Label>
            <Form.Control
              type="date"
              name="end_date"
              value={values.end_date}
              onChange={change}
              min={values.start_date || undefined}
            />
          </Form.Group>
        </div>

        <div className="d-flex gap-2">
          <Button type="submit" disabled={busy}>
            {busy ? 'Creating...' : 'Create project'}
          </Button>
          <Button as={Link} to="/projects" variant="light" disabled={busy}>
            Cancel
          </Button>
        </div>
      </Form>
    </MainCard>
  );
}
