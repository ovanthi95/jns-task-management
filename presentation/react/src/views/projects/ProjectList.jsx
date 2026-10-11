import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

import Badge from 'react-bootstrap/Badge';
import Button from 'react-bootstrap/Button';
import ButtonGroup from 'react-bootstrap/ButtonGroup';
import Form from 'react-bootstrap/Form';
import Modal from 'react-bootstrap/Modal';
import Table from 'react-bootstrap/Table';

import MainCard from 'components/MainCard';
import { getSessionUser } from 'services/auth/sessionService';
import { getProjects } from 'services/projects/projectListService';
import { updateProject } from 'services/projects/projectUpdateService';

const filters = ['All', 'Active', 'Inactive', 'Completed'];

function statusVariant(status) {
  if (status === 'Completed') return 'success';
  if (status === 'Inactive') return 'secondary';
  return 'primary';
}

function progressText(project) {
  return `${Number(project.completed_tasks || 0)} / ${Number(project.total_tasks || 0)} completed`;
}

export default function ProjectList() {
  const [projects, setProjects] = useState([]);
  const [permissions, setPermissions] = useState([]);
  const [filter, setFilter] = useState('All');
  const [loading, setLoading] = useState(true);
  const [savingId, setSavingId] = useState(null);
  const [error, setError] = useState('');
  const [reactivationProject, setReactivationProject] = useState(null);
  const [pendingStatus, setPendingStatus] = useState('Active');
  const [password, setPassword] = useState('');
  const [reactivationError, setReactivationError] = useState('');

  const canCreate = permissions.includes('create_projects');
  const canEdit = permissions.includes('edit_projects');

  useEffect(() => {
    let active = true;

    Promise.all([getSessionUser(), getProjects()])
      .then(([user, rows]) => {
        if (!active) return;
        setPermissions(user?.permissions || []);
        setProjects(rows);
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
  }, []);

  const counts = useMemo(
    () => ({
      All: projects.length,
      Active: projects.filter((p) => p.status === 'Active').length,
      Inactive: projects.filter((p) => p.status === 'Inactive').length,
      Completed: projects.filter((p) => p.status === 'Completed').length
    }),
    [projects]
  );

  const visible = useMemo(
    () =>
      filter === 'All'
        ? projects
        : projects.filter((project) => project.status === filter),
    [filter, projects]
  );

  const applyStatus = async (project, status, adminPassword) => {
    setSavingId(project.project_id);
    setError('');

    try {
      const payload = { status };
      if (adminPassword) payload.admin_password = adminPassword;

      const updated = await updateProject(project.project_id, payload);
      setProjects((current) =>
        current.map((item) =>
          item.project_id === updated.project_id ? updated : item
        )
      );
      return true;
    } catch (requestError) {
      if (adminPassword) setReactivationError(requestError.message);
      else setError(requestError.message);
      return false;
    } finally {
      setSavingId(null);
    }
  };

  const requestStatusChange = async (project, status) => {
    if (status === project.status) return;

    if (project.status === 'Completed' && status !== 'Completed') {
      setPassword('');
      setReactivationError('');
      setPendingStatus(status);
      setReactivationProject(project);
      return;
    }

    await applyStatus(project, status);
  };

  const confirmReactivation = async (event) => {
    event.preventDefault();
    if (!reactivationProject || !password) return;

    const ok = await applyStatus(
      reactivationProject,
      pendingStatus,
      password
    );

    if (ok) {
      setReactivationProject(null);
      setPassword('');
      setReactivationError('');
    }
  };

  return (
    <>
      <MainCard
        title="Projects"
        secondary={
          canCreate ? (
            <Button as={Link} to="/projects/new">
              Add project
            </Button>
          ) : null
        }
      >
        <div className="d-flex flex-wrap gap-3 justify-content-between align-items-center mb-3">
          <ButtonGroup aria-label="Project status filter">
            {filters.map((item) => (
              <Button
                key={item}
                variant={filter === item ? 'primary' : 'outline-primary'}
                onClick={() => setFilter(item)}
              >
                {item} ({counts[item]})
              </Button>
            ))}
          </ButtonGroup>
          <span className="text-muted">Showing {visible.length} project(s)</span>
        </div>

        {error && <div className="alert alert-danger">{error}</div>}

        {loading ? (
          <p>Loading projects...</p>
        ) : visible.length === 0 ? (
          <p className="mb-0">No projects found.</p>
        ) : (
          <Table responsive hover align="middle">
            <thead>
              <tr>
                <th>Project</th>
                <th>Dates</th>
                <th>Task progress</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {visible.map((project) => (
                <tr key={project.project_id}>
                  <td>
                    <Link
                      to={`/projects/${project.project_id}/tasks`}
                      className="fw-semibold text-decoration-none"
                    >
                      {project.project_name}
                    </Link>
                    <div className="d-flex align-items-center gap-2 flex-wrap"><Button as={Link} to={"/projects/" + project.project_id + "/tasks"} size="sm" variant="outline-secondary">Tasks</Button>{canEdit && <Button as={Link} to={"/projects/" + project.project_id + "/edit"} size="sm" variant="outline-primary">Edit project</Button>}</div>
                    {project.description && (
                      <div>
                        <small className="text-muted">{project.description}</small>
                      </div>
                    )}
                  </td>
                  <td>
                    <div>{project.start_date || '—'}</div>
                    <small className="text-muted">to {project.end_date || '—'}</small>
                  </td>
                  <td>{progressText(project)}</td>
                  <td>
                    {canEdit ? (
                      <Form.Select
                        size="sm"
                        value={project.status}
                        disabled={savingId === project.project_id}
                        onChange={(event) =>
                          requestStatusChange(project, event.target.value)
                        }
                      >
                        <option value="Active">Active — {progressText(project)}</option>
                        <option value="Inactive">Inactive</option>
                        <option value="Completed">Completed</option>
                      </Form.Select>
                    ) : (
                      <Badge bg={statusVariant(project.status)}>
                        {project.status}
                      </Badge>
                    )}
                  </td>

                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </MainCard>

      <Modal
        show={Boolean(reactivationProject)}
        onHide={() => setReactivationProject(null)}
        centered
      >
        <Form onSubmit={confirmReactivation}>
          <Modal.Header closeButton>
            <Modal.Title>Reopen completed project</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <p>
              Enter your password to change this completed project to {pendingStatus}.
            </p>
            <Form.Control
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="current-password"
              required
              autoFocus
              isInvalid={Boolean(reactivationError)}
            />
            <Form.Control.Feedback type="invalid">
              {reactivationError}
            </Form.Control.Feedback>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={() => setReactivationProject(null)}>
              Cancel
            </Button>
            <Button type="submit" disabled={!password}>
              Confirm
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>
    </>
  );
}
