// API 05 UI - Project list
// Owner: Jesse

import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

import Alert from 'react-bootstrap/Alert';
import Badge from 'react-bootstrap/Badge';
import Button from 'react-bootstrap/Button';
import ButtonGroup from 'react-bootstrap/ButtonGroup';
import Table from 'react-bootstrap/Table';

import MainCard from 'components/MainCard';
import { getProjects } from 'services/projects/projectListService';

const filters = ['All', 'Active', 'Inactive', 'Completed'];

function statusVariant(status) {
  if (status === 'Completed') return 'success';
  if (status === 'Inactive') return 'secondary';
  return 'primary';
}

function progressText(project) {
  return `${project.completed_tasks || 0} / ${project.total_tasks || 0} completed`;
}

export default function ProjectList() {
  const [projects, setProjects] = useState([]);
  const [filter, setFilter] = useState('All');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;

    getProjects()
      .then((rows) => {
        if (active) setProjects(rows);
      })
      .catch((err) => {
        if (active) setError(err.message);
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
      Active: projects.filter((project) => project.status === 'Active').length,
      Inactive: projects.filter((project) => project.status === 'Inactive').length,
      Completed: projects.filter((project) => project.status === 'Completed').length
    }),
    [projects]
  );

  const visibleProjects = useMemo(
    () =>
      filter === 'All'
        ? projects
        : projects.filter((project) => project.status === filter),
    [filter, projects]
  );

  return (
    <MainCard
      title="Projects"
      secondary={
        <div className="d-flex gap-2">
          <Button as={Link} to="/history" variant="outline-secondary">
            History
          </Button>
          <Button as={Link} to="/projects/new">
            Add project
          </Button>
        </div>
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

        <span className="text-muted">
          Showing {visibleProjects.length} project{visibleProjects.length === 1 ? '' : 's'}
        </span>
      </div>

      {error && <Alert variant="danger">{error}</Alert>}

      {loading ? (
        <p>Loading projects...</p>
      ) : visibleProjects.length === 0 ? (
        <p className="mb-0">
          No {filter === 'All' ? '' : filter.toLowerCase()} projects found.
        </p>
      ) : (
        <Table responsive hover align="middle">
          <thead>
            <tr>
              <th>Project</th>
              <th>Dates</th>
              <th>Task progress</th>
              <th>Status</th>
              <th />
            </tr>
          </thead>

          <tbody>
            {visibleProjects.map((project) => (
              <tr key={project.project_id}>
                <td>
                  <Link
                    to={`/projects/${project.project_id}/tasks`}
                    className="fw-semibold text-decoration-none"
                  >
                    {project.project_name}
                  </Link>

                  {project.description && (
                    <div>
                      <small className="text-muted">
                        {project.description}
                      </small>
                    </div>
                  )}
                </td>

                <td>
                  <div>{project.start_date || '—'}</div>
                  <small className="text-muted">
                    to {project.end_date || '—'}
                  </small>
                </td>

                <td>{progressText(project)}</td>

                <td>
                  <Badge bg={statusVariant(project.status)}>
                    {project.status}
                  </Badge>
                </td>

                <td className="text-end">
                  <ButtonGroup size="sm">
                    <Button
                      as={Link}
                      to={`/projects/${project.project_id}/edit`}
                      variant="outline-primary"
                    >
                      Edit
                    </Button>
                    <Button
                      as={Link}
                      to={`/projects/${project.project_id}/tasks`}
                      variant="outline-secondary"
                    >
                      Tasks
                    </Button>
                  </ButtonGroup>
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}
    </MainCard>
  );
}
