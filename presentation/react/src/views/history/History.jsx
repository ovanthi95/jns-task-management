import { useEffect, useRef, useState } from 'react';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
import Table from 'react-bootstrap/Table';
import MainCard from 'components/MainCard';
import { getHistory } from 'services/audit/historyService';

const tabs = ['Project', 'Task', 'User'];

function formatDateTime(value) {
  if (!value) return '—';
  return new Date(value).toLocaleString();
}

function formatField(fieldName) {
  if (!fieldName) return 'Created';

  return fieldName
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

function formatValue(value) {
  if (value === null || value === undefined || value === '') {
    return '—';
  }

  if (typeof value !== 'object') {
    return String(value);
  }

  return Object.entries(value)
    .map(([key, item]) => {
      const label = key
        .split('_')
        .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
        .join(' ');

      return `${label}: ${item ?? '—'}`;
    })
    .join(' · ');
}

export default function History() {
  const [entityType, setEntityType] = useState('Project');
  const [search, setSearch] = useState('');
  const [changedBy, setChangedBy] = useState('');
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');
  const [items, setItems] = useState([]);
  const [currentItems, setCurrentItems] = useState([]);
  const [changedByOptions, setChangedByOptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [scrollToHistory, setScrollToHistory] = useState(false);
  const historySectionRef = useRef(null);

  useEffect(() => {
    let active = true;

    const timer = setTimeout(() => {
      setLoading(true);
      setError('');

      getHistory({
        entityType,
        search,
        changedBy,
        from: fromDate,
        to: toDate
      })
        .then((data) => {
          if (!active) return;

          setItems(data.items || []);
          setCurrentItems(data.current_items || []);
          setChangedByOptions(data.changed_by_options || []);
        })
        .catch((err) => {
          if (!active) return;

          setError(err.message);
          setItems([]);
          setCurrentItems([]);
        })
        .finally(() => {
          if (active) setLoading(false);
        });
    }, 250);

    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [entityType, search, changedBy, fromDate, toDate]);

  const switchTab = (tab) => {
    setEntityType(tab);
    setSearch('');
    setChangedBy('');
    setFromDate('');
    setToDate('');
  };

  const clearFilters = () => {
    setSearch('');
    setChangedBy('');
    setFromDate('');
    setToDate('');
  };

  const viewItemHistory = (name) => {
    setSearch(name);
    setChangedBy('');
    setFromDate('');
    setToDate('');
    setScrollToHistory(true);
  };

  const viewProjectTaskHistory = (projectName) => {
    setEntityType('Task');
    setSearch(projectName);
    setChangedBy('');
    setFromDate('');
    setToDate('');
    setScrollToHistory(true);
  };

  useEffect(() => {
    if (!scrollToHistory || loading) return;

    historySectionRef.current?.scrollIntoView({
      behavior: 'smooth',
      block: 'start'
    });

    setScrollToHistory(false);
  }, [scrollToHistory, loading, items]);

  const hasFilters =
    search || changedBy || fromDate || toDate;

  const showCurrentWork =
    entityType === 'Project' || entityType === 'Task';

  return (
    <MainCard title="History">
      <div className="d-flex flex-wrap gap-2 mb-2">
        {tabs.map((tab) => (
          <Button
            key={tab}
            type="button"
            variant={entityType === tab ? 'primary' : 'outline-primary'}
            onClick={() => switchTab(tab)}
          >
            {tab} History
          </Button>
        ))}
      </div>

      <p className="text-muted mb-4">
        Project History shows project-level changes. Task status changes,
        including Kanban moves, appear under Task History.
      </p>

      <div className="border rounded p-3 mb-4">
        <Form.Group className="mb-3" controlId="history-search">
          <Form.Label className="fw-semibold">
            Search {entityType.toLowerCase()} history
          </Form.Label>

          <Form.Control
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder={
              entityType === 'Project'
                ? 'Type a project name you remember...'
                : entityType === 'Task'
                  ? 'Type a task, project, assignee, or person name...'
                  : 'Type a user name or email...'
            }
            autoComplete="off"
          />

          <Form.Text>
            You do not need the exact full name.
          </Form.Text>
        </Form.Group>

        <div className="row g-2">
          <div className="col-md-4">
            <Form.Label>Changed by</Form.Label>

            <Form.Select
              value={changedBy}
              onChange={(event) => setChangedBy(event.target.value)}
            >
              <option value="">All users</option>

              {changedByOptions.map((user) => (
                <option
                  key={user.user_id}
                  value={String(user.user_id)}
                >
                  {user.name}
                </option>
              ))}
            </Form.Select>
          </div>

          <div className="col-md-3">
            <Form.Label>From</Form.Label>

            <Form.Control
              type="date"
              value={fromDate}
              onChange={(event) => setFromDate(event.target.value)}
            />
          </div>

          <div className="col-md-3">
            <Form.Label>To</Form.Label>

            <Form.Control
              type="date"
              value={toDate}
              onChange={(event) => setToDate(event.target.value)}
            />
          </div>

          <div className="col-md-2 d-flex align-items-end">
            <Button
              type="button"
              variant="outline-secondary"
              className="w-100"
              onClick={clearFilters}
              disabled={!hasFilters}
            >
              Clear
            </Button>
          </div>
        </div>
      </div>

      {error && (
        <div className="alert alert-danger" role="alert">
          {error}
        </div>
      )}

      {loading ? (
        <p>Loading History...</p>
      ) : (
        <>
          {showCurrentWork && (
            <div className="mb-5">
              <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-2">
                <h5 className="mb-0">
                  Current ongoing {entityType === 'Project' ? 'projects' : 'tasks'}
                </h5>

                <span className="text-muted">
                  {currentItems.length} ongoing
                </span>
              </div>

              {currentItems.length === 0 ? (
                <p className="text-muted mb-0">
                  No ongoing {entityType.toLowerCase()}s match the current search.
                </p>
              ) : entityType === 'Project' ? (
                <Table responsive hover align="middle">
                  <thead>
                    <tr>
                      <th>Project</th>
                      <th>Status</th>
                      <th>Progress</th>
                      <th>Start date</th>
                      <th>End date</th>
                      <th />
                    </tr>
                  </thead>

                  <tbody>
                    {currentItems.map((project) => (
                      <tr key={project.entity_id}>
                        <td className="fw-semibold">
                          {project.entity_name}
                        </td>
                        <td>{project.status}</td>
                        <td>
                          {project.completed_tasks} / {project.total_tasks} tasks completed
                        </td>
                        <td>{project.start_date || '—'}</td>
                        <td>{project.end_date || '—'}</td>
                        <td className="text-end">
                          <div className="d-flex justify-content-end gap-2">
                            <Button
                              type="button"
                              size="sm"
                              variant="outline-primary"
                              onClick={() => viewItemHistory(project.entity_name)}
                            >
                              Project history
                            </Button>

                            <Button
                              type="button"
                              size="sm"
                              variant="primary"
                              onClick={() => viewProjectTaskHistory(project.entity_name)}
                            >
                              Task activity
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              ) : (
                <Table responsive hover align="middle">
                  <thead>
                    <tr>
                      <th>Task</th>
                      <th>Project</th>
                      <th>Assignee</th>
                      <th>Status</th>
                      <th>Priority</th>
                      <th>Due date</th>
                      <th />
                    </tr>
                  </thead>

                  <tbody>
                    {currentItems.map((task) => (
                      <tr key={task.entity_id}>
                        <td className="fw-semibold">
                          {task.entity_name}
                        </td>
                        <td>{task.project_name}</td>
                        <td>
                          {task.assignees?.length
                            ? task.assignees.map((item) => item.name).join(', ')
                            : 'Unassigned'}
                        </td>
                        <td>{task.status}</td>
                        <td>{task.priority}</td>
                        <td>{task.due_date || '—'}</td>
                        <td className="text-end">
                          <Button
                            type="button"
                            size="sm"
                            variant="outline-primary"
                            onClick={() => viewItemHistory(task.entity_name)}
                          >
                            View history
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              )}
            </div>
          )}

          <div ref={historySectionRef}>
            <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-2">
              <h5 className="mb-0">
                {entityType} history records
              </h5>

              <span className="text-muted">
                {items.length} matching record
                {items.length === 1 ? '' : 's'}
              </span>
            </div>

          {items.length === 0 ? (
            <p className="mb-0 text-muted">
              No matching {entityType.toLowerCase()} history found.
            </p>
          ) : (
            <Table responsive hover align="middle">
              <thead>
                <tr>
                  <th>Date / time</th>
                  <th>{entityType}</th>
                  <th>Changed by</th>
                  <th>Change</th>
                  <th>From</th>
                  <th>To</th>
                </tr>
              </thead>

              <tbody>
                {items.map((item) => (
                  <tr key={item.history_id}>
                    <td>{formatDateTime(item.created_at)}</td>

                    <td>
                      <div className="fw-semibold">
                        {item.entity_name || `${entityType} #${item.entity_id}`}
                      </div>

                      {item.description && (
                        <small className="text-muted">
                          {item.description}
                        </small>
                      )}
                    </td>

                    <td>{item.changed_by_name}</td>
                    <td>{formatField(item.field_name)}</td>
                    <td>{formatValue(item.old_value)}</td>
                    <td>{formatValue(item.new_value)}</td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
          </div>
        </>
      )}
    </MainCard>
  );
}
