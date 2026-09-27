import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import Accordion from 'react-bootstrap/Accordion';
import Badge from 'react-bootstrap/Badge';
import Button from 'react-bootstrap/Button';
import Table from 'react-bootstrap/Table';
import MainCard from 'components/MainCard';
import {
  getUserWorkloadTasks,
  getWorkload
} from 'services/workload/workloadService';

function hours(value) {
  const parsed = Number(value || 0);
  return parsed.toFixed(2).replace(/\.00$/, '');
}

function priorityVariant(priority) {
  if (priority === 'Urgent') return 'danger';
  if (priority === 'High') return 'warning';
  if (priority === 'Medium') return 'primary';
  return 'secondary';
}

export default function WorkloadUser() {
  const { userId } = useParams();
  const [user, setUser] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [dueSoonDays, setDueSoonDays] = useState(7);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;

    Promise.all([
      getWorkload(),
      getUserWorkloadTasks(userId)
    ])
      .then(([workload, taskRows]) => {
        if (!active) return;

        const selected = (workload.users || []).find(
          (item) => Number(item.user_id) === Number(userId)
        );

        if (!selected) {
          throw new Error('User not found in the active workload.');
        }

        setUser(selected);
        setTasks(taskRows || []);
        setDueSoonDays(workload.due_soon_days || 7);
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
  }, [userId]);

  const projects = useMemo(() => {
    const grouped = new Map();

    tasks.forEach((task) => {
      const key = Number(task.project_id);

      if (!grouped.has(key)) {
        grouped.set(key, {
          project_id: task.project_id,
          project_name: task.project_name,
          tasks: []
        });
      }

      grouped.get(key).tasks.push(task);
    });

    return Array.from(grouped.values()).sort((a, b) =>
      a.project_name.localeCompare(b.project_name)
    );
  }, [tasks]);

  if (loading) {
    return (
      <MainCard title="User Workload">
        <p>Loading user workload...</p>
      </MainCard>
    );
  }

  if (error || !user) {
    return (
      <MainCard title="User Workload">
        <div className="alert alert-danger" role="alert">
          {error || 'Unable to load user workload.'}
        </div>

        <Button
          as={Link}
          to="/workload"
          variant="outline-primary"
        >
          Back to Workload
        </Button>
      </MainCard>
    );
  }

  return (
    <MainCard
      title={`${user.first_name} ${user.last_name} — Workload`}
      secondary={
        <Button
          as={Link}
          to="/workload"
          variant="outline-primary"
        >
          Back to Workload
        </Button>
      }
    >
      <div className="border rounded p-3 mb-4">
        <div className="row g-3">
          <div className="col-md-6 col-xl-3">
            <div className="text-muted small">Role</div>
            <div className="fw-semibold">{user.role_name}</div>
          </div>

          <div className="col-md-6 col-xl-3">
            <div className="text-muted small">Availability</div>
            <div className="fw-semibold">
              {user.availability || 'Not set'}
            </div>
          </div>

          <div className="col-md-6 col-xl-3">
            <div className="text-muted small">Email</div>
            <div className="fw-semibold">{user.email}</div>
          </div>

          <div className="col-md-6 col-xl-3">
            <div className="text-muted small">Current projects</div>
            <div className="fw-semibold">{user.project_count}</div>
          </div>
        </div>
      </div>

      <div className="row g-3 mb-4">
        <div className="col-sm-6 col-xl-3">
          <div className="border rounded p-3 h-100">
            <div className="text-muted small">Open tasks</div>
            <div className="fs-4 fw-semibold">
              {user.active_tasks}
            </div>
          </div>
        </div>

        <div className="col-sm-6 col-xl-3">
          <div className="border rounded p-3 h-100">
            <div className="text-muted small">Overdue</div>
            <div className="fs-4 fw-semibold">
              {user.overdue_tasks}
            </div>
          </div>
        </div>

        <div className="col-sm-6 col-xl-3">
          <div className="border rounded p-3 h-100">
            <div className="text-muted small">
              Due within {dueSoonDays} days
            </div>
            <div className="fs-4 fw-semibold">
              {user.due_soon_tasks}
            </div>
          </div>
        </div>

        <div className="col-sm-6 col-xl-3">
          <div className="border rounded p-3 h-100">
            <div className="text-muted small">
              Estimated open hours
            </div>
            <div className="fs-4 fw-semibold">
              {hours(user.estimated_hours)}
            </div>
          </div>
        </div>
      </div>

      <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3">
        <div>
          <h5 className="mb-1">Assigned projects and tasks</h5>
          <div className="text-muted">
            Expand a project to see the tasks currently assigned to this user.
          </div>
        </div>

        <Badge bg="secondary">
          {projects.length} project{projects.length === 1 ? '' : 's'}
        </Badge>
      </div>

      {projects.length === 0 ? (
        <div className="border rounded p-4 text-muted">
          This user has no open assigned tasks in Active projects.
        </div>
      ) : (
        <Accordion alwaysOpen>
          {projects.map((project, index) => {
            const overdueCount = project.tasks.filter(
              (task) => Boolean(task.is_overdue)
            ).length;

            return (
              <Accordion.Item
                eventKey={String(index)}
                key={project.project_id}
              >
                <Accordion.Header>
                  <div className="d-flex flex-wrap align-items-center gap-2 w-100 me-3">
                    <span className="fw-semibold">
                      {project.project_name}
                    </span>

                    <Badge bg="secondary">
                      {project.tasks.length} task
                      {project.tasks.length === 1 ? '' : 's'}
                    </Badge>

                    {overdueCount > 0 && (
                      <Badge bg="danger">
                        {overdueCount} overdue
                      </Badge>
                    )}
                  </div>
                </Accordion.Header>

                <Accordion.Body>
                  <Table responsive hover align="middle" className="mb-0">
                    <thead>
                      <tr>
                        <th>Task</th>
                        <th>Status</th>
                        <th>Priority</th>
                        <th>Start date</th>
                        <th>Due date</th>
                        <th>Est. hours</th>
                        <th />
                      </tr>
                    </thead>

                    <tbody>
                      {project.tasks.map((task) => (
                        <tr key={task.task_id}>
                          <td className="fw-semibold">
                            {task.title}
                          </td>

                          <td>{task.status_name}</td>

                          <td>
                            <Badge
                              bg={priorityVariant(task.priority_name)}
                            >
                              {task.priority_name}
                            </Badge>
                          </td>

                          <td>{task.start_date || '—'}</td>

                          <td>
                            {task.due_date || '—'}

                            {Boolean(task.is_overdue) && (
                              <Badge bg="danger" className="ms-2">
                                Overdue
                              </Badge>
                            )}

                            {!Boolean(task.is_overdue)
                              && Boolean(task.is_due_soon) && (
                                <Badge
                                  bg="warning"
                                  className="ms-2"
                                >
                                  Due soon
                                </Badge>
                              )}
                          </td>

                          <td>{hours(task.estimated_hours)}</td>

                          <td className="text-end">
                            <Button
                              as={Link}
                              to={
                                `/projects/${task.project_id}`
                                + `/tasks/${task.task_id}`
                              }
                              size="sm"
                              variant="outline-primary"
                            >
                              Open task
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </Table>
                </Accordion.Body>
              </Accordion.Item>
            );
          })}
        </Accordion>
      )}
    </MainCard>
  );
}
