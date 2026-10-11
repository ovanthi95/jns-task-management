import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';

import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';

import MainCard from 'components/MainCard';
import { getProjects } from 'services/projects/projectListService';
import { getProjectMembers } from 'services/projects/projectMembersService';
import { updateProject } from 'services/projects/projectUpdateService';
import { getUsers } from 'services/users/userListService';

export default function ProjectEdit() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [values, setValues] = useState(null);
  const [members, setMembers] = useState([]);
  const [selected, setSelected] = useState([]);
  const [memberSearch, setMemberSearch] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;

    Promise.all([
      getProjects(),
      getUsers(),
      getProjectMembers(projectId)
    ])
      .then(([projects, users, projectMembers]) => {
        if (!active) return;

        const project = projects.find(
          (item) => String(item.project_id) === String(projectId)
        );

        if (!project) {
          setError('Project not found.');
          return;
        }

        const memberMap = new Map(
          users.map((user) => [Number(user.user_id), user])
        );

        projectMembers.forEach((member) => {
          const id = Number(member.user_id);
          const existing = memberMap.get(id);

          memberMap.set(id, {
            ...(existing || {}),
            ...member
          });
        });

        const allMembers = Array.from(memberMap.values()).sort((a, b) =>
          `${a.first_name} ${a.last_name}`.localeCompare(
            `${b.first_name} ${b.last_name}`
          )
        );

        setValues({
          project_name: project.project_name || '',
          description: project.description || '',
          start_date: project.start_date || '',
          end_date: project.end_date || '',
          status: project.status || 'Active'
        });
        setMembers(allMembers);
        setSelected(projectMembers.map((member) => Number(member.user_id)));
      })
      .catch((requestError) => {
        if (active) setError(requestError.message);
      });

    return () => {
      active = false;
    };
  }, [projectId]);

  const filteredMembers = useMemo(() => {
    const query = memberSearch.trim().toLowerCase();

    if (!query) return members;

    return members.filter((user) => {
      const name = `${user.first_name} ${user.last_name}`.toLowerCase();
      const role = (user.role_name || '').toLowerCase();
      const status = (user.status || '').toLowerCase();

      return (
        name.includes(query)
        || role.includes(query)
        || status.includes(query)
      );
    });
  }, [memberSearch, members]);

  const change = (event) => {
    setValues((current) => ({
      ...current,
      [event.target.name]: event.target.value
    }));
  };

  const toggleMember = (userId) => {
    const id = Number(userId);
    const member = members.find((item) => Number(item.user_id) === id);

    if (member?.is_creator) return;

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
      await updateProject(projectId, {
        project_name: values.project_name,
        description: values.description || null,
        start_date: values.start_date || null,
        end_date: values.end_date || null,
        status: values.status,
        member_ids: selected
      });
      navigate('/projects');
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  };

  if (!values) {
    return (
      <MainCard title="Edit project">
        {error || 'Loading project...'}
      </MainCard>
    );
  }

  return (
    <MainCard title="Edit project">
      <Form onSubmit={submit} className="col-lg-8">
        <Form.Group className="mb-3">
          <Form.Label>Project name</Form.Label>
          <Form.Control
            name="project_name"
            value={values.project_name}
            onChange={change}
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
          <Form.Label>Status</Form.Label>
          <Form.Select
            name="status"
            value={values.status}
            onChange={change}
          >
            <option value="Active">Active</option>
            <option value="Inactive">Inactive</option>
            <option value="Completed">Completed</option>
          </Form.Select>
          <Form.Text>
            Reopening a completed project is handled from the project list
            because it requires your password.
          </Form.Text>
        </Form.Group>

        <Form.Group className="mb-3">
          <Form.Label>Project members</Form.Label>

          <Form.Control
            type="search"
            placeholder="Search members by name, role or status..."
            value={memberSearch}
            onChange={(event) => setMemberSearch(event.target.value)}
            className="mb-3"
            aria-label="Search project members"
          />

          <div className="border rounded p-3">
            {filteredMembers.length === 0 ? (
              <small className="text-muted">
                No members match your search.
              </small>
            ) : (
              filteredMembers.map((user) => {
                const isCreator = Boolean(user.is_creator);
                const isInactive = String(user.status).toLowerCase() !== 'active';

                return (
                  <Form.Check
                    key={user.user_id}
                    className="mb-2"
                    type="checkbox"
                    id={`edit-project-member-${user.user_id}`}
                    checked={selected.includes(Number(user.user_id))}
                    disabled={isCreator}
                    onChange={() => toggleMember(user.user_id)}
                    label={`${user.first_name} ${user.last_name} — ${user.role_name}${isCreator ? ' (creator)' : isInactive ? ' (inactive)' : ''}`}
                  />
                );
              })
            )}

            <small className="text-muted d-block mt-2">
              {selected.length} member{selected.length === 1 ? '' : 's'} selected
            </small>
          </div>
        </Form.Group>

        {error && <div className="alert alert-danger">{error}</div>}

        <Button type="submit" disabled={busy}>
          {busy ? 'Saving...' : 'Save changes'}
        </Button>
        <Link to="/projects" className="btn btn-link ms-2">
          Cancel
        </Link>
      </Form>
    </MainCard>
  );
}
