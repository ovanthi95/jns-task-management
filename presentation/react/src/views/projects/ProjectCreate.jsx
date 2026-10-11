import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';

import MainCard from 'components/MainCard';
import { getSessionUser } from 'services/auth/sessionService';
import { createProject } from 'services/projects/projectCreateService';
import { getUsers } from 'services/users/userListService';

const empty = {
  project_name: '',
  description: '',
  start_date: '',
  end_date: ''
};

export default function ProjectCreate() {
  const navigate = useNavigate();
  const [values, setValues] = useState(empty);
  const [members, setMembers] = useState([]);
  const [selected, setSelected] = useState([]);
  const [memberSearch, setMemberSearch] = useState('');
  const [currentUser, setCurrentUser] = useState(null);
  const [access, setAccess] = useState('checking');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;

    getSessionUser()
      .then(async (user) => {
        if (!active) return;

        setCurrentUser(user);
        const allowed = user?.permissions?.includes('create_projects');
        setAccess(allowed ? 'allowed' : 'denied');

        if (!allowed) return;

        try {
          const users = await getUsers();
          if (!active) return;
          setMembers(users.filter((item) => item.status === 'Active'));
        } catch {
          if (active) setMembers([]);
        }
      })
      .catch(() => {
        if (active) setAccess('denied');
      });

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (currentUser?.user_id) {
      setSelected((ids) =>
        Array.from(new Set([Number(currentUser.user_id), ...ids]))
      );
    }
  }, [currentUser]);

  const sortedMembers = useMemo(
    () =>
      [...members].sort((a, b) =>
        `${a.first_name} ${a.last_name}`.localeCompare(
          `${b.first_name} ${b.last_name}`
        )
      ),
    [members]
  );

  const filteredMembers = useMemo(() => {
    const query = memberSearch.trim().toLowerCase();

    if (!query) return sortedMembers;

    return sortedMembers.filter((user) => {
      const name = `${user.first_name} ${user.last_name}`.toLowerCase();
      const role = (user.role_name || '').toLowerCase();

      return name.includes(query) || role.includes(query);
    });
  }, [memberSearch, sortedMembers]);

  const change = (event) => {
    setValues((current) => ({
      ...current,
      [event.target.name]: event.target.value
    }));
  };

  const toggleMember = (userId) => {
    const id = Number(userId);
    if (id === Number(currentUser?.user_id)) return;

    setSelected((current) =>
      current.includes(id)
        ? current.filter((item) => item !== id)
        : [...current, id]
    );
  };

  const submit = async (event) => {
    event.preventDefault();
    setBusy(true);
    setError('');

    try {
      const project = await createProject({
        project_name: values.project_name,
        description: values.description || '',
        start_date: values.start_date || null,
        end_date: values.end_date || null,
        member_ids: selected
      });
      navigate(`/projects/${project.project_id}/tasks`);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  };

  if (access === 'checking') {
    return <MainCard title="Add project">Checking access...</MainCard>;
  }

  if (access === 'denied') {
    return (
      <MainCard title="Add project">
        Project creation permission required.
      </MainCard>
    );
  }

  return (
    <MainCard title="Add project">
      <Form onSubmit={submit} className="col-lg-8">
        <Form.Group className="mb-3">
          <Form.Label>Project name</Form.Label>
          <Form.Control
            name="project_name"
            value={values.project_name}
            onChange={change}
            maxLength={150}
            required
          />
        </Form.Group>

        <Form.Group className="mb-3">
          <Form.Label>Description</Form.Label>
          <Form.Control
            as="textarea"
            rows={4}
            name="description"
            value={values.description}
            onChange={change}
          />
        </Form.Group>

        <div className="row">
          <Form.Group className="col-md-6 mb-3">
            <Form.Label>Start date</Form.Label>
            <Form.Control
              type="date"
              name="start_date"
              value={values.start_date}
              onChange={change}
            />
          </Form.Group>
          <Form.Group className="col-md-6 mb-3">
            <Form.Label>End date</Form.Label>
            <Form.Control
              type="date"
              name="end_date"
              value={values.end_date}
              onChange={change}
            />
          </Form.Group>
        </div>

        <Form.Group className="mb-3">
          <Form.Label>Project members</Form.Label>

          {members.length > 0 && (
            <Form.Control
              type="search"
              placeholder="Search members by name or role..."
              value={memberSearch}
              onChange={(event) => setMemberSearch(event.target.value)}
              className="mb-3"
              aria-label="Search project members"
            />
          )}

          <div className="border rounded p-3">
            {sortedMembers.length === 0 ? (
              <small className="text-muted">
                You will be added as the project creator. Other members can be
                added when the user list is available.
              </small>
            ) : filteredMembers.length === 0 ? (
              <small className="text-muted">
                No members match your search.
              </small>
            ) : (
              filteredMembers.map((user) => {
                const isCreator =
                  Number(user.user_id) === Number(currentUser?.user_id);

                return (
                  <Form.Check
                    key={user.user_id}
                    className="mb-2"
                    type="checkbox"
                    id={`project-member-${user.user_id}`}
                    checked={selected.includes(Number(user.user_id))}
                    disabled={isCreator}
                    onChange={() => toggleMember(user.user_id)}
                    label={`${user.first_name} ${user.last_name} — ${user.role_name}${isCreator ? ' (creator)' : ''}`}
                  />
                );
              })
            )}

            {selected.length > 0 && (
              <small className="text-muted d-block mt-2">
                {selected.length} member{selected.length === 1 ? '' : 's'} selected
              </small>
            )}
          </div>
        </Form.Group>

        {error && <div className="alert alert-danger">{error}</div>}

        <Button type="submit" disabled={busy}>
          {busy ? 'Adding project...' : 'Add project'}
        </Button>
        <Link to="/projects" className="btn btn-link ms-2">
          Cancel
        </Link>
      </Form>
    </MainCard>
  );
}
