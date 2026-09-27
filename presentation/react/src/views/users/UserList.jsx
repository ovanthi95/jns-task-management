// API 02 UI - User list
// Owner: Manatka

import { useMemo, useState } from 'react';

// react-bootstrap
import Alert from 'react-bootstrap/Alert';
import Badge from 'react-bootstrap/Badge';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
import Spinner from 'react-bootstrap/Spinner';
import Table from 'react-bootstrap/Table';
import { Link } from 'react-router-dom';

// project-imports
import MainCard from 'components/MainCard';
import { useUserList } from 'logic/users/useUserList';

// ==============================|| USERS - LIST (API 02) ||============================== //

export default function UserList() {
  const { users, loading, error } = useUserList();
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('All');
  const [statusFilter, setStatusFilter] = useState('All');

  const roleOptions = useMemo(
    () =>
      Array.from(new Set(users.map((user) => user.role_name).filter(Boolean))).sort(),
    [users]
  );

  const visibleUsers = useMemo(() => {
    const term = search.trim().toLowerCase();

    return users.filter((user) => {
      const fullName = `${user.first_name || ''} ${user.last_name || ''}`.trim().toLowerCase();
      const email = (user.email || '').toLowerCase();

      const matchesSearch = !term || fullName.includes(term) || email.includes(term);
      const matchesRole = roleFilter === 'All' || user.role_name === roleFilter;
      const matchesStatus = statusFilter === 'All' || user.status === statusFilter;

      return matchesSearch && matchesRole && matchesStatus;
    });
  }, [users, search, roleFilter, statusFilter]);

  let body;

  if (loading) {
    body = (
      <div className="text-center py-4">
        <Spinner animation="border" size="sm" className="me-2" />
        Loading users...
      </div>
    );
  } else if (error) {
    body = (
      <Alert variant={error.status === 403 ? 'warning' : 'danger'} className="mb-0">
        {error.status === 403 ? 'Your role is not permitted to view the user list.' : 'Could not load users. Please try again.'}
      </Alert>
    );
  } else {
    body = (
      <>
        <div className="row g-2 mb-3">
          <div className="col-lg-5">
            <Form.Control
              type="search"
              placeholder="Search by name or email"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </div>

          <div className="col-md-4 col-lg-3">
            <Form.Select
              value={roleFilter}
              onChange={(event) => setRoleFilter(event.target.value)}
              aria-label="Filter users by role"
            >
              <option value="All">All roles</option>
              {roleOptions.map((role) => (
                <option key={role} value={role}>
                  {role}
                </option>
              ))}
            </Form.Select>
          </div>

          <div className="col-md-4 col-lg-2">
            <Form.Select
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value)}
              aria-label="Filter users by status"
            >
              <option value="All">All statuses</option>
              <option value="Active">Active</option>
              <option value="Inactive">Inactive</option>
            </Form.Select>
          </div>

          <div className="col-md-4 col-lg-2 d-flex align-items-center">
            <span className="text-muted">
              {visibleUsers.length} user{visibleUsers.length === 1 ? '' : 's'}
            </span>
          </div>
        </div>

        {visibleUsers.length === 0 ? (
          <p className="text-muted text-center py-3 mb-0">No users match the selected filters.</p>
        ) : (
          <Table responsive hover className="mb-0" align="middle">
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Role</th>
                <th>Availability</th>
                <th>Status</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {visibleUsers.map((user) => (
                <tr key={user.user_id}>
                  <td>{user.first_name} {user.last_name}</td>
                  <td>{user.email}</td>
                  <td>{user.role_name}</td>
                  <td>{user.availability || '—'}</td>
                  <td>
                    <Badge bg={user.status === 'Active' ? 'success' : 'secondary'}>{user.status}</Badge>
                  </td>
                  <td className="text-end">
                    <Button
                      as={Link}
                      to={`/users/${user.user_id}/edit`}
                      size="sm"
                      variant="outline-primary"
                    >
                      Edit
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </>
    );
  }

  return (
    <MainCard
      className="table-card"
      title="Users"
      subheader={<p className="mb-0">All users in your organisation</p>}
      secondary={
        <Button as={Link} to="/users/new" size="sm">
          <i className="ph ph-user-plus me-1" />
          Create user
        </Button>
      }
    >
      {body}
    </MainCard>
  );
}
