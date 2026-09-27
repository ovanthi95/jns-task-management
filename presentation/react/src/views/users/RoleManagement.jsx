import { useEffect, useMemo, useState } from 'react';

import Alert from 'react-bootstrap/Alert';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
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

export default function RoleManagement() {
  const [roles, setRoles] = useState([]);
  const [permissions, setPermissions] = useState([]);
  const [draft, setDraft] = useState(emptyRole);
  const [editing, setEditing] = useState({});
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const load = () =>
    getRoles()
      .then((data) => {
        setRoles(data.roles || []);
        setPermissions(data.permissions || []);
        setEditing(
          Object.fromEntries(
            (data.roles || []).map((role) => [
              role.role_id,
              {
                role_name: role.role_name,
                description: role.description || '',
                is_active: role.is_active,
                permission_codes: role.permission_codes || []
              }
            ])
          )
        );
      });

  useEffect(() => {
    load().catch((err) => setError(err.message));
  }, []);

  const categories = useMemo(() => {
    const map = new Map();

    permissions.forEach((permission) => {
      if (!map.has(permission.category)) {
        map.set(permission.category, []);
      }
      map.get(permission.category).push(permission);
    });

    return Array.from(map.entries());
  }, [permissions]);

  const togglePermission = (value, code) => {
    const current = value.permission_codes || [];
    return current.includes(code)
      ? current.filter((item) => item !== code)
      : [...current, code];
  };

  const create = async (event) => {
    event.preventDefault();
    setError('');
    setSuccess('');

    try {
      await createRole(draft);
      setDraft(emptyRole);
      await load();
      setSuccess('Role created.');
    } catch (err) {
      setError(err.message);
    }
  };

  const save = async (roleId) => {
    setError('');
    setSuccess('');

    try {
      await updateRole(roleId, editing[roleId]);
      await load();
      setSuccess('Role updated.');
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <MainCard title="Role Management">
      {error && <Alert variant="danger">{error}</Alert>}
      {success && <Alert variant="success">{success}</Alert>}

      <h5>Create role</h5>

      <Form onSubmit={create} className="border rounded p-3 mb-4">
        <div className="row g-3">
          <div className="col-md-4">
            <Form.Label>Role name</Form.Label>
            <Form.Control
              value={draft.role_name}
              onChange={(event) =>
                setDraft((current) => ({
                  ...current,
                  role_name: event.target.value
                }))
              }
              required
            />
          </div>

          <div className="col-md-6">
            <Form.Label>Description</Form.Label>
            <Form.Control
              value={draft.description}
              onChange={(event) =>
                setDraft((current) => ({
                  ...current,
                  description: event.target.value
                }))
              }
            />
          </div>

          <div className="col-md-2 d-flex align-items-end">
            <Button type="submit" className="w-100">
              Create
            </Button>
          </div>
        </div>

        <PermissionChooser
          categories={categories}
          selected={draft.permission_codes}
          onToggle={(code) =>
            setDraft((current) => ({
              ...current,
              permission_codes: togglePermission(current, code)
            }))
          }
        />
      </Form>

      <h5>Existing roles</h5>

      <Table responsive hover align="top">
        <thead>
          <tr>
            <th>Role</th>
            <th>Description</th>
            <th>Active</th>
            <th>Permissions</th>
            <th />
          </tr>
        </thead>

        <tbody>
          {roles.map((role) => {
            const value = editing[role.role_id] || role;

            return (
              <tr key={role.role_id}>
                <td>
                  <Form.Control
                    value={value.role_name}
                    disabled={role.is_protected}
                    onChange={(event) =>
                      setEditing((current) => ({
                        ...current,
                        [role.role_id]: {
                          ...value,
                          role_name: event.target.value
                        }
                      }))
                    }
                  />
                </td>

                <td>
                  <Form.Control
                    value={value.description || ''}
                    disabled={role.is_protected}
                    onChange={(event) =>
                      setEditing((current) => ({
                        ...current,
                        [role.role_id]: {
                          ...value,
                          description: event.target.value
                        }
                      }))
                    }
                  />
                </td>

                <td>
                  <Form.Check
                    type="switch"
                    checked={Boolean(value.is_active)}
                    disabled={role.is_protected}
                    onChange={(event) =>
                      setEditing((current) => ({
                        ...current,
                        [role.role_id]: {
                          ...value,
                          is_active: event.target.checked
                        }
                      }))
                    }
                  />
                </td>

                <td style={{ minWidth: 320 }}>
                  {role.is_protected ? (
                    <span className="text-muted">
                      Protected system role — all permissions.
                    </span>
                  ) : (
                    <PermissionChooser
                      categories={categories}
                      selected={value.permission_codes || []}
                      compact
                      onToggle={(code) =>
                        setEditing((current) => ({
                          ...current,
                          [role.role_id]: {
                            ...value,
                            permission_codes:
                              togglePermission(value, code)
                          }
                        }))
                      }
                    />
                  )}
                </td>

                <td className="text-end">
                  {!role.is_protected && (
                    <Button
                      size="sm"
                      onClick={() => save(role.role_id)}
                    >
                      Save
                    </Button>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </Table>
    </MainCard>
  );
}

function PermissionChooser({
  categories,
  selected,
  onToggle,
  compact = false
}) {
  return (
    <div className={compact ? '' : 'mt-3'}>
      {categories.map(([category, items]) => (
        <div key={category} className="mb-2">
          <div className="fw-semibold">{category}</div>

          <div className="d-flex flex-wrap gap-3 mt-1">
            {items.map((permission) => (
              <Form.Check
                key={permission.code}
                type="checkbox"
                id={`permission-${permission.code}-${compact ? 'edit' : 'new'}`}
                label={permission.label}
                checked={selected.includes(permission.code)}
                onChange={() => onToggle(permission.code)}
                title={permission.description}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
