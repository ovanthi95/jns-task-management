// API 07 UI - Task list
// Owner: Edward

import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import Alert from 'react-bootstrap/Alert';
import Badge from 'react-bootstrap/Badge';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
import Spinner from 'react-bootstrap/Spinner';
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
      .catch((err) => {
        if (active) setError(err.message);
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

  const visibleTasks = useMemo(() => {
    const term = search.trim().toLowerCase();
    const today = localDateKey();

    return tasks.filter((task) => {
      const matchesSearch =
        !term ||
        (task.title || '').toLowerCase().includes(term) ||
        (task.description || '').toLowerCase().includes(term);

      const matchesStatus =
        statusFilter === 'All' || String(task.status_id) === statusFilter;

      const matchesPriority =
        priorityFilter === 'All' || String(task.priority_id) === priorityFilter;

      const matchesAssignee =
        assigneeFilter === 'All' ||
        task.assignees?.some(
          (item) => String(item.user_id) === assigneeFilter
        );

      let matchesDue = true;

      if (dueFilter === 'No due date') {
        matchesDue = !task.due_date;
      } else if (dueFilter !== 'All') {
        const isOpen = task.status_name !== 'Completed';

        if (!task.due_date || !isOpen) {
          matchesDue = false;
        } else if (dueFilter === 'Overdue') {
          matchesDue = task.due_date < today;
        } else if (dueFilter === 'Due today') {
          matchesDue = task.due_date === today;
        } else if (dueFilter === 'Upcoming') {
          matchesDue = task.due_date > today;
        }
      }

      return (
        matchesSearch &&
        matchesStatus &&
        matchesPriority &&
        matchesAssignee &&
        matchesDue
      );
    });
  }, [
    tasks,
    search,
    statusFilter,
    priorityFilter,
    assigneeFilter,
    dueFilter
  ]);

  const hasActiveFilters =
    search ||
    statusFilter !== 'All' ||
    priorityFilter !== 'All' ||
    assigneeFilter !== 'All' ||
    dueFilter !== 'All';

  const clearFilters = () => {
    setSearch('');
    setStatusFilter('All');
    setPriorityFilter('All');
    setAssigneeFilter('All');
    setDueFilter('All');
  };

  return (
    <MainCard
      title={
        options?.project?.project_name
          ? `Tasks — ${options.project.project_name}`
          : 'Tasks'
      }
      secondary={
        options?.can_create ? (
          <Button as={Link} to={`/projects/${projectId}/tasks/new`}>
            Add task
          </Button>
        ) : null
      }
    >
      <div className="d-flex flex-wrap gap-3 align-items-center mb-3">
        <Link to="/projects">← Back to projects</Link>

        {options?.project && (
          <Badge
            bg={options.project.status === 'Active' ? 'primary' : 'secondary'}
          >
            {options.project.status}
          </Badge>
        )}

        <span className="text-muted">
          {completed} / {tasks.length} completed
        </span>

        {loading && <Spinner animation="border" size="sm" />}
      </div>

      {options?.project?.status !== 'Active' && options?.project && (
        <Alert variant="info">
          This project is {options.project.status.toLowerCase()}.
          Existing tasks can be viewed, but new tasks cannot be added.
        </Alert>
      )}

      {error && <Alert variant="danger">{error}</Alert>}

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
              <Form.Select
                value={statusFilter}
                onChange={(event) => setStatusFilter(event.target.value)}
              >
                <option value="All">All statuses</option>
                {options?.task_statuses?.map((item) => (
                  <option key={item.status_id} value={String(item.status_id)}>
                    {item.status_name}
                  </option>
                ))}
              </Form.Select>
            </div>

            <div className="col-md-6 col-lg-2">
              <Form.Select
                value={priorityFilter}
                onChange={(event) => setPriorityFilter(event.target.value)}
              >
                <option value="All">All priorities</option>
                {options?.priorities?.map((item) => (
                  <option key={item.priority_id} value={String(item.priority_id)}>
                    {item.priority_name}
                  </option>
                ))}
              </Form.Select>
            </div>

            <div className="col-md-6 col-lg-2">
              <Form.Select
                value={assigneeFilter}
                onChange={(event) => setAssigneeFilter(event.target.value)}
              >
                <option value="All">All assignees</option>
                {options?.users?.map((item) => (
                  <option key={item.user_id} value={String(item.user_id)}>
                    {item.name}
                  </option>
                ))}
              </Form.Select>
            </div>

            <div className="col-md-6 col-lg-2">
              <Form.Select
                value={dueFilter}
                onChange={(event) => setDueFilter(event.target.value)}
              >
                <option value="All">All due dates</option>
                <option value="Overdue">Overdue</option>
                <option value="Due today">Due today</option>
                <option value="Upcoming">Upcoming</option>
                <option value="No due date">No due date</option>
              </Form.Select>
            </div>
          </div>

          <div className="d-flex justify-content-between align-items-center gap-2 mt-3">
            <span className="text-muted">
              Showing {visibleTasks.length} of {tasks.length} tasks
            </span>

            {hasActiveFilters && (
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
        <p>Loading tasks...</p>
      ) : tasks.length === 0 ? (
        <p className="mb-0">No tasks have been added to this project yet.</p>
      ) : visibleTasks.length === 0 ? (
        <p className="mb-0">No tasks match the selected filters.</p>
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
              <th className="text-end">Est. hrs</th>
            </tr>
          </thead>

          <tbody>
            {visibleTasks.map((task) => (
              <tr key={task.task_id}>
                <td>
                  <div className="fw-semibold">{task.title}</div>
                  {task.description && (
                    <small className="text-muted">{task.description}</small>
                  )}
                </td>

                <td>
                  {task.assignees?.length
                    ? task.assignees
                        .map(
                          (item) =>
                            `${item.first_name} ${item.last_name}`
                        )
                        .join(', ')
                    : '—'}
                </td>

                <td>{task.task_type_name}</td>
                <td>{task.priority_name}</td>

                <td>
                  <Badge bg={statusVariant(task.status_name)}>
                    {task.status_name}
                  </Badge>
                </td>

                <td>{task.due_date || '—'}</td>
                <td className="text-end">{task.estimated_hours || '—'}</td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}
    </MainCard>
  );
}
