// API 12 UI - Update user
// Owner: Ovanthi

import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import Alert from 'react-bootstrap/Alert';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
import Spinner from 'react-bootstrap/Spinner';

import MainCard from 'components/MainCard';
import { getSessionUser } from 'services/auth/sessionService';
import { getUsers } from 'services/users/userListService';
import { updateUser } from 'services/users/userUpdateService';
import { getRoles } from 'services/users/roleService';

export default function UserEdit() {
  const { userId } = useParams();
  const [currentUser, setCurrentUser] = useState(null);
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [values, setValues] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    let active = true;

    Promise.all([getSessionUser(), getUsers(), getRoles()])
      .then(([sessionUser, rows, roleData]) => {
        if (!active) return;

        setCurrentUser(sessionUser);
        setUsers(rows);
        setRoles((roleData.roles || []).filter((role) => role.is_active));

        const user = rows.find(
          (item) => String(item.user_id) === String(userId)
        );

        if (!user) {
          setError('User not found.');
          return;
        }

        setValues({
          first_name: user.first_name || '',
          last_name: user.last_name || '',
          email: user.email || '',
          role_name: user.role_name || '',
          availability: user.availability || '',
          status: user.status || 'Active'
        });
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
  }, [userId]);

  const canManageUsers =
    (currentUser?.permissions || []).includes('manage_users');

  const editingSelf =
    Number(currentUser?.user_id) === Number(userId);

  const roleOptions = roles;

  const change = (name, value) => {
    setValues((current) => ({ ...current, [name]: value }));
  };

  const submit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError('');
    setSuccess('');

    try {
      const updated = await updateUser(userId, {
        first_name: values.first_name,
        last_name: values.last_name,
        email: values.email,
        role_name: values.role_name,
        availability: values.availability || null,
        status: values.status
      });

      setValues({
        first_name: updated.first_name || '',
        last_name: updated.last_name || '',
        email: updated.email || '',
        role_name: updated.role_name || '',
        availability: updated.availability || '',
        status: updated.status || 'Active'
      });
      setSuccess('User updated.');
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <MainCard title="Edit user">
        <Spinner animation="border" size="sm" /> Loading user...
      </MainCard>
    );
  }

  if (!canManageUsers) {
    return (
      <MainCard title="Edit user">
        <Alert variant="warning">User management permission required.</Alert>
        <Link to="/users">Back to users</Link>
      </MainCard>
    );
  }

  if (!values) {
    return (
      <MainCard title="Edit user">
        <Alert variant="danger">{error || 'User not found.'}</Alert>
      </MainCard>
    );
  }

  return (
    <MainCard title="Edit user">
      {error && <Alert variant="danger">{error}</Alert>}
      {success && <Alert variant="success">{success}</Alert>}

      <Form onSubmit={submit} className="col-lg-8">
        <div className="row">
          <Form.Group className="col-md-6 mb-3">
            <Form.Label>First name</Form.Label>
            <Form.Control
              value={values.first_name}
              onChange={(event) =>
                change('first_name', event.target.value)
              }
              required
            />
          </Form.Group>

          <Form.Group className="col-md-6 mb-3">
            <Form.Label>Last name</Form.Label>
            <Form.Control
              value={values.last_name}
              onChange={(event) =>
                change('last_name', event.target.value)
              }
              required
            />
          </Form.Group>
        </div>

        <Form.Group className="mb-3">
          <Form.Label>Email</Form.Label>
          <Form.Control
            type="email"
            value={values.email}
            onChange={(event) => change('email', event.target.value)}
            required
          />
        </Form.Group>

        <div className="row">
          <Form.Group className="col-md-6 mb-3">
            <Form.Label>Role</Form.Label>
            <Form.Select
              value={values.role_name}
              disabled={editingSelf}
              onChange={(event) =>
                change('role_name', event.target.value)
              }
            >
              {roleOptions.map((role) => (
                <option key={role.role_id} value={role.role_name}>
                  {role.role_name}
                </option>
              ))}
            </Form.Select>
          </Form.Group>

          <Form.Group className="col-md-6 mb-3">
            <Form.Label>Status</Form.Label>
            <Form.Select
              value={values.status}
              disabled={editingSelf}
              onChange={(event) => change('status', event.target.value)}
            >
              <option value="Active">Active</option>
              <option value="Inactive">Inactive</option>
            </Form.Select>
          </Form.Group>
        </div>

        <Form.Group className="mb-3">
          <Form.Label>Availability</Form.Label>
          <Form.Control
            value={values.availability}
            onChange={(event) =>
              change('availability', event.target.value)
            }
            placeholder="e.g. Full-time, Part-time"
          />
        </Form.Group>

        {editingSelf && (
          <Alert variant="info">
            You can update your profile fields, but you cannot change your
            own role or deactivate the account you are signed in with.
          </Alert>
        )}

        <Button type="submit" disabled={saving}>
          {saving ? 'Saving...' : 'Save changes'}
        </Button>

        <Link to="/users" className="btn btn-link ms-2">
          Cancel
        </Link>
      </Form>
    </MainCard>
  );
}
