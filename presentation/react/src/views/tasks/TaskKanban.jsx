import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import Badge from 'react-bootstrap/Badge';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';

import MainCard from 'components/MainCard';
import { getTaskOptions, getTasks } from 'services/tasks/taskListService';
import { updateTaskStatus } from 'services/tasks/taskUpdateService';

function priorityVariant(priority) {
  if (priority === 'Urgent') return 'danger';
  if (priority === 'High') return 'warning';
  if (priority === 'Medium') return 'primary';
  return 'secondary';
}

function todayKey() {
  const now = new Date();
  return [
    now.getFullYear(),
    String(now.getMonth() + 1).padStart(2, '0'),
    String(now.getDate()).padStart(2, '0')
  ].join('-');
}

export default function TaskKanban() {
  const { projectId } = useParams();
  const [tasks, setTasks] = useState([]);
  const [options, setOptions] = useState(null);
  const [draggedTaskId, setDraggedTaskId] = useState(null);
  const [busyTaskId, setBusyTaskId] = useState(null);
  const [search, setSearch] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

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

  const currentUser = options?.current_user;
  const canChangeAny =
    currentUser?.permissions?.includes('change_any_task_status');
  const canCompleteAssigned =
    currentUser?.permissions?.includes('complete_assigned_tasks');
  const canViewAll =
    currentUser?.permissions?.includes('view_all_tasks');

  const visibleTasks = useMemo(() => {
    const term = search.trim().toLowerCase();

    if (!term) return tasks;

    return tasks.filter((task) => {
      const assignees = task.assignees
        ?.map((item) => `${item.first_name} ${item.last_name}`)
        .join(' ')
        .toLowerCase();

      return task.title?.toLowerCase().includes(term)
        || task.description?.toLowerCase().includes(term)
        || task.priority_name?.toLowerCase().includes(term)
        || assignees?.includes(term);
    });
  }, [tasks, search]);

  const taskById = (taskId) =>
    tasks.find((task) => Number(task.task_id) === Number(taskId));

  const isAssignee = (task) =>
    task.assignees?.some(
      (item) => Number(item.user_id) === Number(currentUser?.user_id)
    );

  const canDrag = (task) =>
    !busyTaskId
    && (
      canChangeAny
      || (
        canCompleteAssigned
        && isAssignee(task)
        && task.status_name !== 'Completed'
      )
    );

  const canDrop = (taskId, statusName) => {
    const task = taskById(taskId);
    if (!task || task.status_name === statusName) return false;
    if (canChangeAny) return true;

    return canCompleteAssigned
      && isAssignee(task)
      && statusName === 'Completed';
  };

  const dropTask = async (event, status) => {
    event.preventDefault();

    const taskId = Number(
      event.dataTransfer.getData('text/plain') || draggedTaskId
    );

    if (!taskId || !canDrop(taskId, status.status_name)) {
      setDraggedTaskId(null);
      return;
    }

    setBusyTaskId(taskId);
    setError('');

    try {
      const updated = await updateTaskStatus(
        taskId,
        Number(status.status_id)
      );

      setTasks((current) =>
        current.map((task) =>
          Number(task.task_id) === taskId
            ? {
                ...task,
                status_id: updated.status_id,
                status_name: updated.status_name,
                updated_at: updated.updated_at
              }
            : task
        )
      );
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusyTaskId(null);
      setDraggedTaskId(null);
    }
  };

  if (loading) return <MainCard title="Kanban">Loading board...</MainCard>;

  if (!options) {
    return <MainCard title="Kanban">{error || 'Unable to load board.'}</MainCard>;
  }

  const today = todayKey();

  return (
    <MainCard
      title={`Kanban — ${options.project.project_name}`}
      secondary={
        <div className="d-flex gap-2">
          <Button
            as={Link}
            to={`/projects/${projectId}/tasks`}
            variant="outline-primary"
          >
            List view
          </Button>
          {options.can_create && (
            <Button as={Link} to={`/projects/${projectId}/tasks/new`}>
              Add task
            </Button>
          )}
        </div>
      }
    >
      <div className="d-flex flex-wrap justify-content-between gap-3 align-items-center mb-3">
        <Link to="/projects">← Back to projects</Link>
        <Form.Control
          type="search"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Search tasks on board"
          style={{ maxWidth: 320 }}
        />
      </div>

      {!canChangeAny && canCompleteAssigned && (
        <div className="alert alert-info">
          You can move only your own assigned tasks to Completed.
        </div>
      )}

      {!canChangeAny && !canCompleteAssigned && (
        <div className="alert alert-secondary">
          This board is read-only for your role.
        </div>
      )}

      {error && <div className="alert alert-danger">{error}</div>}

      <div className="d-flex gap-3 overflow-auto pb-3" style={{ alignItems: 'flex-start' }}>
        {options.task_statuses.map((status) => {
          const columnTasks = visibleTasks.filter(
            (task) => task.status_name === status.status_name
          );

          return (
            <div
              key={status.status_id}
              className="border rounded p-2 flex-shrink-0"
              style={{ width: 285, minHeight: 220 }}
              onDragOver={(event) => {
                if (canChangeAny || (canCompleteAssigned && status.status_name === 'Completed')) {
                  event.preventDefault();
                }
              }}
              onDrop={(event) => dropTask(event, status)}
            >
              <div className="d-flex justify-content-between align-items-center mb-2">
                <strong>{status.status_name}</strong>
                <Badge bg="secondary">{columnTasks.length}</Badge>
              </div>

              {columnTasks.map((task) => {
                const overdue =
                  task.due_date
                  && task.due_date < today
                  && task.status_name !== 'Completed';

                return (
                  <div
                    key={task.task_id}
                    draggable={canDrag(task)}
                    onDragStart={(event) => {
                      if (!canDrag(task)) return;
                      event.dataTransfer.setData(
                        'text/plain',
                        String(task.task_id)
                      );
                      setDraggedTaskId(task.task_id);
                    }}
                    onDragEnd={() => setDraggedTaskId(null)}
                    className="border rounded bg-white p-3 mb-2"
                    style={{
                      cursor: canDrag(task) ? 'grab' : 'default',
                      opacity:
                        Number(draggedTaskId) === Number(task.task_id)
                          ? 0.15
                          : busyTaskId === task.task_id
                            ? 0.6
                            : 1
                    }}
                  >
                    <div className="fw-semibold mb-2">{task.title}</div>
                    <div className="mb-2">
                      <Badge bg={priorityVariant(task.priority_name)}>
                        {task.priority_name}
                      </Badge>
                      {overdue && <Badge bg="danger" className="ms-2">Overdue</Badge>}
                    </div>
                    <div className="small mb-1">
                      <strong>Assignee:</strong>{' '}
                      {task.assignees?.length
                        ? task.assignees
                            .map((item) => `${item.first_name} ${item.last_name}`)
                            .join(', ')
                        : 'Unassigned'}
                    </div>
                    <div className="small mb-2">
                      <strong>Due:</strong> {task.due_date || '—'}
                    </div>

                    {(canViewAll || isAssignee(task)) && (
                      <Button
                        as={Link}
                        to={`/projects/${projectId}/tasks/${task.task_id}`}
                        size="sm"
                        variant="outline-primary"
                      >
                        Open
                      </Button>
                    )}
                  </div>
                );
              })}
            </div>
          );
        })}
      </div>
    </MainCard>
  );
}
