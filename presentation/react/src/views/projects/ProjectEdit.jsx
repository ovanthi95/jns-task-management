import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';

import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';

import MainCard from 'components/MainCard';
import { getProjects } from 'services/projects/projectListService';
import { updateProject } from 'services/projects/projectUpdateService';

export default function ProjectEdit() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [values, setValues] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;

    getProjects()
      .then((projects) => {
        if (!active) return;
        const project = projects.find(
          (item) => String(item.project_id) === String(projectId)
        );

        if (!project) {
          setError('Project not found.');
          return;
        }

        setValues({
          project_name: project.project_name || '',
          description: project.description || '',
          start_date: project.start_date || '',
          end_date: project.end_date || '',
          status: project.status || 'Active'
        });
      })
      .catch((requestError) => {
        if (active) setError(requestError.message);
      });

    return () => {
      active = false;
    };
  }, [projectId]);

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
      await updateProject(projectId, {
        project_name: values.project_name,
        description: values.description || null,
        start_date: values.start_date || null,
        end_date: values.end_date || null,
        status: values.status
      });
      navigate('/projects');
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  };

  if (!values) {
    return (
      <MainCard title="Edit project">
        {error || 'Loading project...'}
      </MainCard>
    );
  }

  return (
    <MainCard title="Edit project">
      <Form onSubmit={submit} className="col-lg-8">
        <Form.Group className="mb-3">
          <Form.Label>Project name</Form.Label>
          <Form.Control
            name="project_name"
            value={values.project_name}
            onChange={change}
            required
          />
        </Form.Group>

        <Form.Group className="mb-3">
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
          <Form.Group className="col-md-6 mb-3">
            <Form.Label>Start date</Form.Label>
            <Form.Control
              type="date"
              name="start_date"
              value={values.start_date}
              onChange={change}
            />
          </Form.Group>
          <Form.Group className="col-md-6 mb-3">
            <Form.Label>End date</Form.Label>
            <Form.Control
              type="date"
              name="end_date"
              value={values.end_date}
              onChange={change}
            />
          </Form.Group>
        </div>

        <Form.Group className="mb-3">
          <Form.Label>Status</Form.Label>
          <Form.Select
            name="status"
            value={values.status}
            onChange={change}
          >
            <option value="Active">Active</option>
            <option value="Inactive">Inactive</option>
            <option value="Completed">Completed</option>
          </Form.Select>
          <Form.Text>
            Reopening a completed project is handled from the project list
            because it requires your password.
          </Form.Text>
        </Form.Group>

        {error && <div className="alert alert-danger">{error}</div>}

        <Button type="submit" disabled={busy}>
          {busy ? 'Saving...' : 'Save changes'}
        </Button>
        <Link to="/projects" className="btn btn-link ms-2">
          Cancel
        </Link>
      </Form>
    </MainCard>
  );
}
