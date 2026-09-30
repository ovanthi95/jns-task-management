import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import Badge from 'react-bootstrap/Badge';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
import Table from 'react-bootstrap/Table';
import MainCard from 'components/MainCard';
import { getWorkload } from 'services/workload/workloadService';

function hours(value) {
  const parsed = Number(value || 0);
  return parsed.toFixed(2).replace(/\.00$/, '');
}

export default function Workload() {
  const [users, setUsers] = useState([]);
  const [dueSoonDays, setDueSoonDays] = useState(7);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('All');
  const [availabilityFilter, setAvailabilityFilter] = useState('All');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;

    getWorkload()
      .then((data) => {
        if (!active) return;
        setUsers(data.users || []);
        setDueSoonDays(data.due_soon_days || 7);
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

  const roleOptions = useMemo(
    () =>
      Array.from(
        new Set(users.map((user) => user.role_name).filter(Boolean))
      ).sort(),
    [users]
  );

  const availabilityOptions = useMemo(
    () =>
      Array.from(
        new Set(users.map((user) => user.availability).filter(Boolean))
      ).sort(),
    [users]
  );

  const visibleUsers = useMemo(() => {
    const term = search.trim().toLowerCase();

    return users.filter((user) => {
      const name =
        `${user.first_name} ${user.last_name}`.trim().toLowerCase();

      const matchesSearch =
        !term
        || name.includes(term)
        || user.email?.toLowerCase().includes(term)
        || user.current_projects?.some(
          (project) => project.toLowerCase().includes(term)
        );

      const matchesRole =
        roleFilter === 'All'
        || user.role_name === roleFilter;

      const matchesAvailability =
        availabilityFilter === 'All'
        || (user.availability || 'Not set') === availabilityFilter;

      return (
        matchesSearch
        && matchesRole
        && matchesAvailability
      );
    });
  }, [
    users,
    search,
    roleFilter,
    availabilityFilter
  ]);

  const totals = useMemo(
    () =>
      users.reduce(
        (result, user) => ({
          activeTasks:
            result.activeTasks + Number(user.active_tasks || 0),
          overdue:
            result.overdue + Number(user.overdue_tasks || 0),
          dueSoon:
            result.dueSoon + Number(user.due_soon_tasks || 0),
          estimatedHours:
            result.estimatedHours
            + Number(user.estimated_hours || 0)
        }),
        {
          activeTasks: 0,
          overdue: 0,
          dueSoon: 0,
          estimatedHours: 0
        }
      ),
    [users]
  );

  const clearFilters = () => {
    setSearch('');
    setRoleFilter('All');
    setAvailabilityFilter('All');
  };

  const hasFilters =
    search
    || roleFilter !== 'All'
    || availabilityFilter !== 'All';

  return (
    <MainCard title="Workload">
      <p className="text-muted">
        Current workload includes open tasks in Active projects.
        Due soon covers today through the next {dueSoonDays} days.
      </p>

      {error && (
        <div className="alert alert-danger" role="alert">
          {error}
        </div>
      )}

      {!loading && (
        <div className="row g-3 mb-4">
          <div className="col-sm-6 col-xl-3">
            <div className="border rounded p-3 h-100">
              <div className="text-muted small">Open tasks</div>
              <div className="fs-4 fw-semibold">
                {totals.activeTasks}
              </div>
            </div>
          </div>

          <div className="col-sm-6 col-xl-3">
            <div className="border rounded p-3 h-100">
              <div className="text-muted small">Overdue</div>
              <div className="fs-4 fw-semibold">
                {totals.overdue}
              </div>
            </div>
          </div>

          <div className="col-sm-6 col-xl-3">
            <div className="border rounded p-3 h-100">
              <div className="text-muted small">
                Due within {dueSoonDays} days
              </div>
              <div className="fs-4 fw-semibold">
                {totals.dueSoon}
              </div>
            </div>
          </div>

          <div className="col-sm-6 col-xl-3">
            <div className="border rounded p-3 h-100">
              <div className="text-muted small">
                Estimated open hours
              </div>
              <div className="fs-4 fw-semibold">
                {hours(totals.estimatedHours)}
              </div>
            </div>
          </div>
        </div>
      )}

      {!loading && users.length > 0 && (
        <div className="border rounded p-3 mb-4">
          <div className="row g-2">
            <div className="col-lg-6">
              <Form.Control
                type="search"
                placeholder="Search user, email, or project"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />
            </div>

            <div className="col-md-6 col-lg-3">
              <Form.Select
                value={roleFilter}
                onChange={(event) => setRoleFilter(event.target.value)}
              >
                <option value="All">All roles</option>
                {roleOptions.map((role) => (
                  <option key={role} value={role}>
                    {role}
                  </option>
                ))}
              </Form.Select>
            </div>

            <div className="col-md-6 col-lg-3">
              <Form.Select
                value={availabilityFilter}
                onChange={(event) =>
                  setAvailabilityFilter(event.target.value)
                }
              >
                <option value="All">All availability</option>
                {availabilityOptions.map((availability) => (
                  <option
                    key={availability}
                    value={availability}
                  >
                    {availability}
                  </option>
                ))}
                {users.some((user) => !user.availability) && (
                  <option value="Not set">Not set</option>
                )}
              </Form.Select>
            </div>
          </div>

          <div className="d-flex justify-content-between align-items-center gap-2 mt-3">
            <span className="text-muted">
              Showing {visibleUsers.length} of {users.length} active users
            </span>

            {hasFilters && (
              <Button
                type="button"
                size="sm"
                variant="outline-secondary"
                onClick={clearFilters}
              >
                Clear filters
              </Button>
            )}
          </div>
        </div>
      )}

      {loading ? (
        <p>Loading workload...</p>
      ) : users.length === 0 ? (
        <p className="mb-0 text-muted">
          No active users found.
        </p>
      ) : (
        <Table responsive hover align="middle">
          <thead>
            <tr>
              <th>User</th>
              <th>Role</th>
              <th>Availability</th>
              <th>Open tasks</th>
              <th>Overdue</th>
              <th>Due soon</th>
              <th>Est. hours</th>
              <th>Current projects</th>
            </tr>
          </thead>

          <tbody>
            {visibleUsers.map((user) => (
              <tr key={user.user_id}>
                <td>
                  <Link
                    to={`/workload/users/${user.user_id}`}
                    className="fw-semibold text-decoration-none"
                  >
                    {user.first_name} {user.last_name} →
                  </Link>

                  <div>
                    <small className="text-muted">
                      {user.email}
                    </small>
                  </div>
                </td>

                <td>{user.role_name}</td>
                <td>{user.availability || 'Not set'}</td>
                <td>{user.active_tasks}</td>

                <td>
                  {Number(user.overdue_tasks) > 0 ? (
                    <Badge bg="danger">
                      {user.overdue_tasks}
                    </Badge>
                  ) : (
                    '0'
                  )}
                </td>

                <td>{user.due_soon_tasks}</td>
                <td>{hours(user.estimated_hours)}</td>

                <td style={{ width: 220, maxWidth: 220 }}>
                  <div
                    title={
                      user.current_projects?.length
                        ? user.current_projects.join(', ')
                        : undefined
                    }
                    style={{
                      width: 220,
                      maxWidth: '100%',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis'
                    }}
                  >
                    {user.current_projects?.length
                      ? user.current_projects.join(', ')
                      : '—'}
                  </div>
                </td>

              </tr>
            ))}
          </tbody>
        </Table>
      )}
    </MainCard>
  );
}
