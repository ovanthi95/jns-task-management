import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import Alert from 'react-bootstrap/Alert';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';

import MainCard from 'components/MainCard';
import { getSessionUser } from 'services/auth/sessionService';
import { getProjects } from 'services/projects/projectListService';
import { updateProject } from 'services/projects/projectUpdateService';

export default function ProjectEdit() {
  const { projectId } = useParams();

  const [values, setValues] = useState(null);
  const [originalStatus, setOriginalStatus] = useState('Active');
  const [progress, setProgress] = useState({ completed: 0, total: 0 });
  const [password, setPassword] = useState('');
  const [access, setAccess] = useState('checking');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [fieldErrors, setFieldErrors] = useState({});
  const [success, setSuccess] = useState('');

  const needsPassword =
    originalStatus === 'Completed' &&
    values?.status !== 'Completed';

  useEffect(() => {
    let active = true;

    Promise.all([getSessionUser(), getProjects()])
      .then(([user, projects]) => {
        if (!active) return;

        setAccess(
          user?.permissions?.includes('edit_projects')
            ? 'allowed'
            : 'denied'
        );

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
        setOriginalStatus(project.status || 'Active');
        setProgress({
          completed: project.completed_tasks || 0,
          total: project.total_tasks || 0
        });
      })
      .catch((err) => setError(err.message));

    return () => {
      active = false;
    };
  }, [projectId]);

  const change = (event) => {
    setValues((current) => ({
      ...current,
      [event.target.name]: event.target.value
    }));
    setFieldErrors((current) => ({
      ...current,
      [event.target.name]: undefined
    }));
  };

  const submit = async (event) => {
    event.preventDefault();
    setBusy(true);
    setError('');
    setFieldErrors({});
    setSuccess('');

    try {
      const payload = {
        project_name: values.project_name.trim(),
        description: values.description.trim(),
        start_date: values.start_date || null,
        end_date: values.end_date || null,
        status: values.status
      };

      if (needsPassword) payload.admin_password = password;

      const updated = await updateProject(projectId, payload);

      setValues({
        project_name: updated.project_name || '',
        description: updated.description || '',
        start_date: updated.start_date || '',
        end_date: updated.end_date || '',
        status: updated.status || 'Active'
      });
      setOriginalStatus(updated.status || 'Active');
      setProgress({
        completed: updated.completed_tasks || 0,
        total: updated.total_tasks || 0
      });
      setPassword('');
      setSuccess('Project updated.');
    } catch (err) {
      setError(err.message);
      setFieldErrors(err.fields || {});
    } finally {
      setBusy(false);
    }
  };

  if (access === 'checking' || !values) {
    return <MainCard title="Edit project">{error || 'Loading project...'}</MainCard>;
  }

  if (access === 'denied') {
    return (
      <MainCard title="Edit project">
        <Alert variant="warning">Project editing permission required.</Alert>
        <Link to="/projects">Back to projects</Link>
      </MainCard>
    );
  }

  return (
    <MainCard title="Edit project">
      {error && <Alert variant="danger">{error}</Alert>}
      {success && <Alert variant="success">{success}</Alert>}

      <Form onSubmit={submit} className="col-lg-8">
        <Form.Group className="mb-3">
          <Form.Label>Project name</Form.Label>
          <Form.Control
            name="project_name"
            value={values.project_name}
            onChange={change}
            maxLength={150}
            required
            isInvalid={Boolean(fieldErrors.project_name)}
          />
          <Form.Control.Feedback type="invalid">
            {fieldErrors.project_name?.[0]}
          </Form.Control.Feedback>
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
              min={values.start_date || undefined}
              value={values.end_date}
              onChange={change}
              isInvalid={Boolean(fieldErrors.end_date)}
            />
            <Form.Control.Feedback type="invalid">
              {fieldErrors.end_date?.[0]}
            </Form.Control.Feedback>
          </Form.Group>
        </div>

        <Form.Group className="mb-3">
          <Form.Label>Status</Form.Label>
          <Form.Select
            name="status"
            value={values.status}
            onChange={change}
          >
            <option value="Active">
              Active — {progress.completed} / {progress.total} completed
            </option>
            <option value="Inactive">Inactive</option>
            <option value="Completed">Completed</option>
          </Form.Select>
        </Form.Group>

        {needsPassword && (
          <Form.Group className="mb-3">
            <Form.Label>Your password</Form.Label>
            <Form.Control
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
              autoComplete="current-password"
              isInvalid={Boolean(fieldErrors.admin_password)}
            />
            <Form.Control.Feedback type="invalid">
              {fieldErrors.admin_password?.[0]}
            </Form.Control.Feedback>
            <Form.Text className="text-muted">
              Required to reopen a completed project.
            </Form.Text>
          </Form.Group>
        )}

        <Button type="submit" disabled={busy || (needsPassword && !password)}>
          {busy ? 'Saving...' : 'Save changes'}
        </Button>

        <Button
          as={Link}
          to="/projects"
          variant="light"
          className="ms-2"
          disabled={busy}
        >
          Cancel
        </Button>
      </Form>
    </MainCard>
  );
}
