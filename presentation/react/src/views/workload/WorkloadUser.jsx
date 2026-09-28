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

        if (!selected) throw new Error('User not found in the active workload.');

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

    return () => { active = false; };
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
    return <MainCard title="User Workload">Loading user workload...</MainCard>;
  }

  if (error || !user) {
    return (
      <MainCard title="User Workload">
        <div className="alert alert-danger">{error || 'Unable to load user workload.'}</div>
        <Button as={Link} to="/workload" variant="outline-primary">
          Back to Workload
        </Button>
      </MainCard>
    );
  }

  return (
    <MainCard
      title={`${user.first_name} ${user.last_name} — Workload`}
      secondary={
        <Button as={Link} to="/workload" variant="outline-primary">
          Back to Workload
        </Button>
      }
    >
      <div className="border rounded p-3 mb-4">
        <div className="row g-3">
          <Info label="Role" value={user.role_name} />
          <Info label="Availability" value={user.availability || 'Not set'} />
          <Info label="Email" value={user.email} />
          <Info label="Current projects" value={user.project_count} />
        </div>
      </div>

      <div className="row g-3 mb-4">
        <Info label="Open tasks" value={user.active_tasks} />
        <Info label="Overdue" value={user.overdue_tasks} />
        <Info label={`Due within ${dueSoonDays} days`} value={user.due_soon_tasks} />
        <Info label="Estimated open hours" value={hours(user.estimated_hours)} />
      </div>

      {projects.length === 0 ? (
        <div className="border rounded p-4 text-muted">
          This user has no open assigned tasks in Active projects.
        </div>
      ) : (
        <Accordion alwaysOpen>
          {projects.map((project, index) => (
            <Accordion.Item eventKey={String(index)} key={project.project_id}>
              <Accordion.Header>
                <span className="fw-semibold">{project.project_name}</span>
                <Badge bg="secondary" className="ms-2">
                  {project.tasks.length}
                </Badge>
              </Accordion.Header>
              <Accordion.Body>
                <Table responsive hover className="mb-0">
                  <thead>
                    <tr>
                      <th>Task</th>
                      <th>Status</th>
                      <th>Priority</th>
                      <th>Start</th>
                      <th>Due</th>
                      <th>Est. hours</th>
                    </tr>
                  </thead>
                  <tbody>
                    {project.tasks.map((task) => (
                      <tr key={task.task_id}>
                        <td>{task.title}</td>
                        <td>{task.status_name}</td>
                        <td>{task.priority_name}</td>
                        <td>{task.start_date || '—'}</td>
                        <td>
                          {task.due_date || '—'}
                          {Boolean(task.is_overdue) && (
                            <Badge bg="danger" className="ms-2">Overdue</Badge>
                          )}
                          {!Boolean(task.is_overdue) && Boolean(task.is_due_soon) && (
                            <Badge bg="warning" className="ms-2">Due soon</Badge>
                          )}
                        </td>
                        <td>{hours(task.estimated_hours)}</td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              </Accordion.Body>
            </Accordion.Item>
          ))}
        </Accordion>
      )}
    </MainCard>
  );
}

function Info({ label, value }) {
  return (
    <div className="col-md-6 col-xl-3">
      <div className="text-muted small">{label}</div>
      <div className="fw-semibold">{value}</div>
    </div>
  );
}
