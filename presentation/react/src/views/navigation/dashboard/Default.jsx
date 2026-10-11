import { useEffect, useMemo, useState } from 'react';

import Badge from 'react-bootstrap/Badge';
import Spinner from 'react-bootstrap/Spinner';
import Table from 'react-bootstrap/Table';

import MainCard from 'components/MainCard';
import { getSessionUser } from 'services/auth/sessionService';
import { getProjects } from 'services/projects/projectListService';
import { getWorkload } from 'services/workload/workloadService';

function projectStatusVariant(status) {
  if (status === 'Completed') return 'success';
  if (status === 'Inactive') return 'secondary';
  return 'primary';
}

function completionPercent(completed, total) {
  const done = Number(completed || 0);
  const all = Number(total || 0);

  if (all <= 0) return 0;
  return Math.min(100, Math.round((done / all) * 100));
}

export default function DefaultPage() {
  const [projects, setProjects] = useState([]);
  const [users, setUsers] = useState([]);
  const [canViewWorkload, setCanViewWorkload] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;

    const loadDashboard = async () => {
      try {
        const [sessionUser, projectRows] = await Promise.all([
          getSessionUser(),
          getProjects()
        ]);

        if (!active) return;

        setProjects(projectRows || []);

        const hasWorkloadPermission = Boolean(
          sessionUser?.permissions?.includes('view_workload')
        );

        setCanViewWorkload(hasWorkloadPermission);

        if (!hasWorkloadPermission) {
          return;
        }

        const workload = await getWorkload();

        if (!active) return;
        setUsers(workload?.users || []);
      } catch (requestError) {
        if (active) setError(requestError.message);
      } finally {
        if (active) setLoading(false);
      }
    };

    loadDashboard();

    return () => {
      active = false;
    };
  }, []);

  const activeProjects = useMemo(
    () => projects.filter((project) => project.status === 'Active'),
    [projects]
  );

  const totals = useMemo(
    () =>
      users.reduce(
        (result, user) => ({
          assigned: result.assigned + Number(user.assigned_tasks || 0),
          completed: result.completed + Number(user.completed_tasks || 0),
          open: result.open + Number(user.active_tasks || 0)
        }),
        { assigned: 0, completed: 0, open: 0 }
      ),
    [users]
  );

  return (
    <>
      <MainCard
        title="Dashboard"
        subheader={
          <p className="mb-0 text-muted">
            Overview of ongoing projects, team workload and task progress.
          </p>
        }
      >
        {error && (
          <div className="alert alert-danger" role="alert">
            {error}
          </div>
        )}

        {loading ? (
          <div className="text-center py-5">
            <Spinner animation="border" size="sm" className="me-2" />
            Loading dashboard...
          </div>
        ) : (
          <>
            <div className="row g-3 mb-4">
              <div className="col-sm-6 col-xl-3">
                <div className="border rounded p-3 h-100">
                  <div className="text-muted small">Ongoing projects</div>
                  <div className="fs-3 fw-semibold">{activeProjects.length}</div>
                </div>
              </div>

              {canViewWorkload && (
                <>
                  <div className="col-sm-6 col-xl-3">
                    <div className="border rounded p-3 h-100">
                      <div className="text-muted small">Active users</div>
                      <div className="fs-3 fw-semibold">{users.length}</div>
                    </div>
                  </div>

                  <div className="col-sm-6 col-xl-3">
                    <div className="border rounded p-3 h-100">
                      <div className="text-muted small">Open assigned tasks</div>
                      <div className="fs-3 fw-semibold">{totals.open}</div>
                    </div>
                  </div>

                  <div className="col-sm-6 col-xl-3">
                    <div className="border rounded p-3 h-100">
                      <div className="text-muted small">Completed tasks</div>
                      <div className="fs-3 fw-semibold">{totals.completed}</div>
                      <small className="text-muted">
                        {totals.completed} of {totals.assigned} assigned
                      </small>
                    </div>
                  </div>
                </>
              )}
            </div>

            <div className="row g-4">
              <div className={canViewWorkload ? 'col-xl-7' : 'col-12'}>
                <MainCard title="Ongoing projects" className="h-100">
                  {activeProjects.length === 0 ? (
                    <p className="text-muted mb-0">No ongoing projects.</p>
                  ) : (
                    <Table responsive hover className="mb-0">
                      <thead>
                        <tr>
                          <th>Project</th>
                          <th>Progress</th>
                          <th>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {activeProjects.map((project) => {
                          const percent = completionPercent(
                            project.completed_tasks,
                            project.total_tasks
                          );

                          return (
                            <tr key={project.project_id}>
                              <td className="fw-semibold">
                                {project.project_name}
                              </td>
                              <td style={{ minWidth: 180 }}>
                                <div className="d-flex justify-content-between small mb-1">
                                  <span>
                                    {Number(project.completed_tasks || 0)} /{' '}
                                    {Number(project.total_tasks || 0)}
                                  </span>
                                  <span>{percent}%</span>
                                </div>
                                <div className="progress" style={{ height: 6 }}>
                                  <div
                                    className="progress-bar"
                                    role="progressbar"
                                    style={{ width: `${percent}%` }}
                                    aria-valuenow={percent}
                                    aria-valuemin="0"
                                    aria-valuemax="100"
                                  />
                                </div>
                              </td>
                              <td>
                                <Badge bg={projectStatusVariant(project.status)}>
                                  {project.status}
                                </Badge>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </Table>
                  )}
                </MainCard>
              </div>

              {canViewWorkload && (
                <div className="col-xl-5">
                  <MainCard title="Team task progress" className="h-100">
                    {users.length === 0 ? (
                      <p className="text-muted mb-0">No active users found.</p>
                    ) : (
                      <Table responsive hover className="mb-0">
                        <thead>
                          <tr>
                            <th>User</th>
                            <th>Completed</th>
                            <th>Progress</th>
                          </tr>
                        </thead>
                        <tbody>
                          {users.map((user) => {
                            const assigned = Number(user.assigned_tasks || 0);
                            const completed = Number(user.completed_tasks || 0);
                            const percent = completionPercent(completed, assigned);

                            return (
                              <tr key={user.user_id}>
                                <td>
                                  <div className="fw-semibold">
                                    {user.first_name} {user.last_name}
                                  </div>
                                  <small className="text-muted">
                                    {user.role_name}
                                  </small>
                                </td>
                                <td>
                                  {completed} / {assigned}
                                </td>
                                <td style={{ minWidth: 110 }}>
                                  <div className="small mb-1">{percent}%</div>
                                  <div className="progress" style={{ height: 5 }}>
                                    <div
                                      className="progress-bar"
                                      role="progressbar"
                                      style={{ width: `${percent}%` }}
                                      aria-valuenow={percent}
                                      aria-valuemin="0"
                                      aria-valuemax="100"
                                    />
                                  </div>
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </Table>
                    )}
                  </MainCard>
                </div>
              )}
            </div>
          </>
        )}
      </MainCard>
    </>
  );
}
