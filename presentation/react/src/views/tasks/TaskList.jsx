import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import Badge from 'react-bootstrap/Badge';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
import Table from 'react-bootstrap/Table';

import MainCard from 'components/MainCard';
import { getTaskOptions, getTasks } from 'services/tasks/taskListService';

function statusVariant(status) {
  if (status === 'Completed') return 'success';
  if (status === 'In Progress') return 'primary';
  if (status === 'Under Review') return 'warning';
  if (status === 'Waiting for Information') return 'info';
  return 'secondary';
}

function localDateKey() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export default function TaskList() {
  const { projectId } = useParams();
  const [tasks, setTasks] = useState([]);
  const [options, setOptions] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const [priorityFilter, setPriorityFilter] = useState('All');
  const [assigneeFilter, setAssigneeFilter] = useState('All');
  const [dueFilter, setDueFilter] = useState('All');

  useEffect(() => {
    let active = true;

    Promise.all([getTasks(projectId), getTaskOptions(projectId)])
      .then(([rows, taskOptions]) => {
        if (!active) return;
        setTasks(rows);
        setOptions(taskOptions);
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
  }, [projectId]);

  const completed = useMemo(
    () => tasks.filter((task) => task.status_name === 'Completed').length,
    [tasks]
  );

  const assigneeOptions = useMemo(() => {
    const people = new Map();

    tasks.forEach((task) => {
      task.assignees?.forEach((assignee) => {
        people.set(String(assignee.user_id), {
          user_id: assignee.user_id,
          name: `${assignee.first_name} ${assignee.last_name}`.trim()
        });
      });
    });

    return Array.from(people.values()).sort((a, b) =>
      a.name.localeCompare(b.name)
    );
  }, [tasks]);

  const visibleTasks = useMemo(() => {
    const term = search.trim().toLowerCase();
    const today = localDateKey();

    return tasks.filter((task) => {
      const matchesSearch =
        !term
        || task.title?.toLowerCase().includes(term)
        || task.description?.toLowerCase().includes(term);

      const matchesStatus =
        statusFilter === 'All' || task.status_name === statusFilter;
      const matchesPriority =
        priorityFilter === 'All' || task.priority_name === priorityFilter;
      const matchesAssignee =
        assigneeFilter === 'All'
        || task.assignees?.some(
          (item) => String(item.user_id) === assigneeFilter
        );

      let matchesDue = true;
      if (dueFilter === 'No due date') {
        matchesDue = !task.due_date;
      } else if (dueFilter !== 'All') {
        const open = task.status_name !== 'Completed';
        if (!task.due_date || !open) matchesDue = false;
        else if (dueFilter === 'Overdue') matchesDue = task.due_date < today;
        else if (dueFilter === 'Due today') matchesDue = task.due_date === today;
        else if (dueFilter === 'Upcoming') matchesDue = task.due_date > today;
      }

      return matchesSearch
        && matchesStatus
        && matchesPriority
        && matchesAssignee
        && matchesDue;
    });
  }, [tasks, search, statusFilter, priorityFilter, assigneeFilter, dueFilter]);

  const currentUser = options?.current_user;
  const canOpenTask = (task) =>
    currentUser?.permissions?.includes('view_all_tasks')
    || task.assignees?.some(
      (item) => Number(item.user_id) === Number(currentUser?.user_id)
    );

  return (
    <MainCard
      title={options?.project?.project_name ? `Tasks — ${options.project.project_name}` : 'Tasks'}
      secondary={
        <div className="d-flex gap-2">
          <Button
            as={Link}
            to={`/projects/${projectId}/kanban`}
            variant="outline-primary"
          >
            Kanban
          </Button>
          {options?.can_create && (
            <Button as={Link} to={`/projects/${projectId}/tasks/new`}>
              Add task
            </Button>
          )}
        </div>
      }
    >
      <div className="d-flex flex-wrap gap-3 align-items-center mb-3">
        <Link to="/projects">← Back to projects</Link>
        {options?.project && (
          <Badge bg={options.project.status === 'Active' ? 'primary' : 'secondary'}>
            {options.project.status}
          </Badge>
        )}
        <span className="text-muted">
          {completed} / {tasks.length} completed
        </span>
      </div>

      {options?.project?.status !== 'Active' && options?.project && (
        <div className="alert alert-info">
          This project is {options.project.status.toLowerCase()}. Existing tasks
          can be viewed, but new tasks cannot be added.
        </div>
      )}

      {error && <div className="alert alert-danger">{error}</div>}

      {!loading && tasks.length > 0 && (
        <div className="border rounded p-3 mb-3">
          <div className="row g-2">
            <div className="col-lg-4">
              <Form.Control
                type="search"
                placeholder="Search task title or description"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />
            </div>
            <div className="col-md-6 col-lg-2">
              <Form.Select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
                <option value="All">All statuses</option>
                {options?.task_statuses?.map((item) => (
                  <option key={item.status_id} value={item.status_name}>
                    {item.status_name}
                  </option>
                ))}
              </Form.Select>
            </div>
            <div className="col-md-6 col-lg-2">
              <Form.Select value={priorityFilter} onChange={(e) => setPriorityFilter(e.target.value)}>
                <option value="All">All priorities</option>
                {options?.priorities?.map((item) => (
                  <option key={item.priority_id} value={item.priority_name}>
                    {item.priority_name}
                  </option>
                ))}
              </Form.Select>
            </div>
            <div className="col-md-6 col-lg-2">
              <Form.Select value={assigneeFilter} onChange={(e) => setAssigneeFilter(e.target.value)}>
                <option value="All">All assignees</option>
                {assigneeOptions.map((item) => (
                  <option key={item.user_id} value={String(item.user_id)}>
                    {item.name}
                  </option>
                ))}
              </Form.Select>
            </div>
            <div className="col-md-6 col-lg-2">
              <Form.Select value={dueFilter} onChange={(e) => setDueFilter(e.target.value)}>
                <option value="All">All due dates</option>
                <option value="Overdue">Overdue</option>
                <option value="Due today">Due today</option>
                <option value="Upcoming">Upcoming</option>
                <option value="No due date">No due date</option>
              </Form.Select>
            </div>
          </div>
        </div>
      )}

      {loading ? (
        <p>Loading tasks...</p>
      ) : visibleTasks.length === 0 ? (
        <p className="mb-0">No tasks match this view.</p>
      ) : (
        <Table responsive hover align="middle">
          <thead>
            <tr>
              <th>Task</th>
              <th>Assignee</th>
              <th>Type</th>
              <th>Priority</th>
              <th>Status</th>
              <th>Due date</th>
            </tr>
          </thead>
          <tbody>
            {visibleTasks.map((task) => (
              <tr key={task.task_id}>
                <td>
                  <div className="fw-semibold d-flex align-items-center gap-2 flex-wrap"><span>{task.title}</span>{canOpenTask(task) && (<Button as={Link} to={"/projects/" + projectId + "/tasks/" + task.task_id} size="sm" variant="outline-primary">Open</Button>)}</div>
                  {task.description && (
                    <small className="text-muted">{task.description}</small>
                  )}
                </td>
                <td>
                  {task.assignees?.length
                    ? task.assignees
                        .map((item) => `${item.first_name} ${item.last_name}`)
                        .join(', ')
                    : 'Unassigned'}
                </td>
                <td>{task.task_type_name === 'Other' && task.other_task_type ? task.other_task_type : task.task_type_name}</td>
                <td>{task.priority_name}</td>
                <td>
                  <Badge bg={statusVariant(task.status_name)}>
                    {task.status_name}
                  </Badge>
                </td>
                <td>{task.due_date || '—'}</td>

              </tr>
            ))}
          </tbody>
        </Table>
      )}
    </MainCard>
  );
}
