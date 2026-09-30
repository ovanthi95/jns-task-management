import { useEffect, useMemo, useState } from 'react';
import Badge from 'react-bootstrap/Badge';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
import Modal from 'react-bootstrap/Modal';
import Table from 'react-bootstrap/Table';

import MainCard from 'components/MainCard';
import {
  createRole,
  getRoles,
  updateRole
} from 'services/users/roleService';

const emptyRole = {
  role_name: '',
  description: '',
  is_active: true,
  permission_codes: []
};

export default function RolesPermissions() {
  const [roles, setRoles] = useState([]);
  const [permissions, setPermissions] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [values, setValues] = useState(emptyRole);
  const [showCreate, setShowCreate] = useState(false);
  const [createValues, setCreateValues] = useState(emptyRole);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const load = async () => {
    setLoading(true);
    setError('');

    try {
      const data = await getRoles();
      setRoles(data.roles || []);
      setPermissions(data.permissions || []);

      if (!selectedId && data.roles?.length) {
        const firstEditable =
          data.roles.find((role) => !role.is_protected)
          || data.roles[0];
        setSelectedId(firstEditable.role_id);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const selectedRole = useMemo(
    () => roles.find(
      (role) => Number(role.role_id) === Number(selectedId)
    ),
    [roles, selectedId]
  );

  useEffect(() => {
    if (!selectedRole) return;

    setValues({
      role_name: selectedRole.role_name || '',
      description: selectedRole.description || '',
      is_active: Boolean(selectedRole.is_active),
      permission_codes: selectedRole.permission_codes || []
    });
    setSuccess('');
    setError('');
  }, [selectedRole]);

  const groupedPermissions = useMemo(() => {
    const groups = new Map();

    permissions.forEach((permission) => {
      if (!groups.has(permission.category)) {
        groups.set(permission.category, []);
      }
      groups.get(permission.category).push(permission);
    });

    return Array.from(groups.entries());
  }, [permissions]);

  const togglePermission = (setter, code) => {
    setter((current) => {
      const selected = new Set(current.permission_codes || []);

      if (selected.has(code)) {
        selected.delete(code);
      } else {
        selected.add(code);
      }

      return {
        ...current,
        permission_codes: Array.from(selected)
      };
    });
  };

  const saveRole = async (event) => {
    event.preventDefault();
    if (!selectedRole || selectedRole.is_protected) return;

    setBusy(true);
    setError('');
    setSuccess('');

    try {
      const updated = await updateRole(selectedRole.role_id, values);

      setRoles((current) =>
        current.map((role) =>
          Number(role.role_id) === Number(updated.role_id)
            ? updated
            : role
        )
      );
      setSuccess('Role permissions saved.');
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const submitCreate = async (event) => {
    event.preventDefault();
    setBusy(true);
    setError('');

    try {
      const created = await createRole(createValues);
      setRoles((current) =>
        [...current, created].sort((a, b) =>
          a.role_name.localeCompare(b.role_name)
        )
      );
      setSelectedId(created.role_id);
      setCreateValues(emptyRole);
      setShowCreate(false);
      setSuccess(`${created.role_name} was created.`);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const permissionChecks = (state, setter, disabled = false) => (
    <div className="row g-3">
      {groupedPermissions.map(([category, items]) => (
        <div className="col-lg-6" key={category}>
          <div className="border rounded p-3 h-100">
            <h6>{category}</h6>

            {items.map((permission) => (
              <Form.Check
                key={permission.code}
                className="mb-2"
                type="checkbox"
                id={`${category}-${permission.code}-${disabled ? 'locked' : 'editable'}`}
                label={
                  <span>
                    <span className="fw-semibold">
                      {permission.label}
                    </span>
                    <span className="d-block text-muted small">
                      {permission.description}
                    </span>
                  </span>
                }
                checked={(state.permission_codes || []).includes(
                  permission.code
                )}
                disabled={disabled}
                onChange={() =>
                  togglePermission(setter, permission.code)
                }
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );

  return (
    <>
      <MainCard
        title="Roles & permissions"
        secondary={
          <Button onClick={() => setShowCreate(true)}>
            Add role
          </Button>
        }
      >
        <p className="text-muted">
          Create roles and control what each role can view or change.
          Admin is a protected system role with full access.
        </p>

        {error && (
          <div className="alert alert-danger" role="alert">
            {error}
          </div>
        )}

        {success && (
          <div className="alert alert-success" role="status">
            {success}
          </div>
        )}

        {loading ? (
          <p>Loading roles...</p>
        ) : (
          <div className="row g-4">
            <div className="col-xl-4">
              <Table hover responsive align="middle" className="mb-0">
                <thead>
                  <tr>
                    <th>Role</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {roles.map((role) => (
                    <tr
                      key={role.role_id}
                      onClick={() => setSelectedId(role.role_id)}
                      style={{ cursor: 'pointer' }}
                      className={
                        Number(selectedId) === Number(role.role_id)
                          ? 'table-active'
                          : ''
                      }
                    >
                      <td>
                        <div className="fw-semibold">
                          {role.role_name}
                        </div>
                        {role.is_protected && (
                          <small className="text-muted">
                            Protected
                          </small>
                        )}
                      </td>
                      <td>
                        <Badge
                          bg={role.is_active ? 'success' : 'secondary'}
                        >
                          {role.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </div>

            <div className="col-xl-8">
              {selectedRole && (
                <Form onSubmit={saveRole}>
                  <div className="row g-3 mb-4">
                    <Form.Group className="col-md-6">
                      <Form.Label>Role name</Form.Label>
                      <Form.Control
                        value={values.role_name}
                        disabled={selectedRole.is_protected}
                        onChange={(event) =>
                          setValues((current) => ({
                            ...current,
                            role_name: event.target.value
                          }))
                        }
                        required
                      />
                    </Form.Group>

                    <Form.Group className="col-md-6">
                      <Form.Label>Status</Form.Label>
                      <Form.Select
                        value={values.is_active ? 'Active' : 'Inactive'}
                        disabled={selectedRole.is_protected}
                        onChange={(event) =>
                          setValues((current) => ({
                            ...current,
                            is_active:
                              event.target.value === 'Active'
                          }))
                        }
                      >
                        <option value="Active">Active</option>
                        <option value="Inactive">Inactive</option>
                      </Form.Select>
                    </Form.Group>

                    <Form.Group className="col-12">
                      <Form.Label>Description</Form.Label>
                      <Form.Control
                        value={values.description}
                        disabled={selectedRole.is_protected}
                        onChange={(event) =>
                          setValues((current) => ({
                            ...current,
                            description: event.target.value
                          }))
                        }
                      />
                    </Form.Group>
                  </div>

                  <h5 className="mb-3">Permissions</h5>

                  {permissionChecks(
                    values,
                    setValues,
                    selectedRole.is_protected
                  )}

                  {!selectedRole.is_protected && (
                    <Button
                      type="submit"
                      className="mt-4"
                      disabled={busy}
                    >
                      {busy ? 'Saving...' : 'Save role'}
                    </Button>
                  )}
                </Form>
              )}
            </div>
          </div>
        )}
      </MainCard>

      <Modal
        show={showCreate}
        onHide={() => setShowCreate(false)}
        size="lg"
        centered
      >
        <Form onSubmit={submitCreate}>
          <Modal.Header closeButton>
            <Modal.Title>Add role</Modal.Title>
          </Modal.Header>

          <Modal.Body>
            <div className="row g-3 mb-4">
              <Form.Group className="col-md-6">
                <Form.Label>Role name</Form.Label>
                <Form.Control
                  value={createValues.role_name}
                  onChange={(event) =>
                    setCreateValues((current) => ({
                      ...current,
                      role_name: event.target.value
                    }))
                  }
                  placeholder="e.g. Team Leader"
                  required
                />
              </Form.Group>

              <Form.Group className="col-md-6">
                <Form.Label>Description</Form.Label>
                <Form.Control
                  value={createValues.description}
                  onChange={(event) =>
                    setCreateValues((current) => ({
                      ...current,
                      description: event.target.value
                    }))
                  }
                  placeholder="Optional"
                />
              </Form.Group>
            </div>

            <h6 className="mb-3">Permissions</h6>
            {permissionChecks(createValues, setCreateValues)}
          </Modal.Body>

          <Modal.Footer>
            <Button
              variant="secondary"
              onClick={() => setShowCreate(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={busy}>
              {busy ? 'Creating...' : 'Create role'}
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>
    </>
  );
}
