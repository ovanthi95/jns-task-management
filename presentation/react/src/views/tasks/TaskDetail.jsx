import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import Badge from 'react-bootstrap/Badge';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';

import MainCard from 'components/MainCard';
import { getComments, createComment } from 'services/tasks/commentService';
import { getFiles, uploadFile } from 'services/tasks/fileService';
import { getTaskOptions, getTasks } from 'services/tasks/taskListService';
import { updateTaskStatus } from 'services/tasks/taskUpdateService';

const MAX_FILE_SIZE = 10 * 1024 * 1024;

function statusVariant(status) {
  if (status === 'Completed') return 'success';
  if (status === 'In Progress') return 'primary';
  if (status === 'Under Review') return 'warning';
  if (status === 'Waiting for Information') return 'info';
  return 'secondary';
}

function formatDateTime(value) {
  return value ? new Date(value).toLocaleString() : '';
}

function formatFileSize(value) {
  if (!value) return '';
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${Math.round(value / 1024)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

export default function TaskDetail() {
  const { projectId, taskId } = useParams();
  const [task, setTask] = useState(null);
  const [options, setOptions] = useState(null);
  const [comments, setComments] = useState([]);
  const [files, setFiles] = useState([]);
  const [commentText, setCommentText] = useState('');
  const [newFile, setNewFile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busyStatus, setBusyStatus] = useState(false);
  const [busyComment, setBusyComment] = useState(false);
  const [busyFile, setBusyFile] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;

    Promise.all([
      getTasks(projectId),
      getTaskOptions(projectId),
      getComments(taskId),
      getFiles(taskId)
    ])
      .then(([tasks, taskOptions, taskComments, taskFiles]) => {
        if (!active) return;

        const found = tasks.find(
          (item) => String(item.task_id) === String(taskId)
        );

        if (!found) {
          setError('Task not found.');
          return;
        }

        setTask(found);
        setOptions(taskOptions);
        setComments(taskComments);
        setFiles(taskFiles);
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
  }, [projectId, taskId]);

  const permissions = options?.current_user?.permissions || [];
  const canViewAll = permissions.includes('view_all_tasks');
  const canEdit = permissions.includes('edit_tasks');
  const canReassign = permissions.includes('reassign_tasks');
  const canChangeStatus = permissions.includes('change_any_task_status');
  const canCompleteAssigned = permissions.includes('complete_assigned_tasks');

  const isAssignee = useMemo(
    () =>
      task?.assignees?.some(
        (item) =>
          Number(item.user_id) === Number(options?.current_user?.user_id)
      ) || false,
    [task, options]
  );

  const completedStatus = options?.task_statuses?.find(
    (item) => item.status_name === 'Completed'
  );

  const changeStatus = async (statusId) => {
    setBusyStatus(true);
    setError('');

    try {
      const updated = await updateTaskStatus(taskId, Number(statusId));
      setTask((current) => ({
        ...current,
        status_id: updated.status_id,
        status_name: updated.status_name,
        updated_at: updated.updated_at
      }));
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusyStatus(false);
    }
  };

  const submitComment = async (event) => {
    event.preventDefault();
    if (!commentText.trim()) return;

    setBusyComment(true);
    setError('');

    try {
      const created = await createComment(taskId, commentText.trim());
      setComments((current) => [...current, created]);
      setCommentText('');
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusyComment(false);
    }
  };

  const chooseFile = (event) => {
    const file = event.target.files?.[0] || null;

    if (file && file.size > MAX_FILE_SIZE) {
      event.target.value = '';
      setNewFile(null);
      setError('Attachment must be 10 MB or smaller.');
      return;
    }

    setError('');
    setNewFile(file);
  };

  const submitFile = async (event) => {
    event.preventDefault();
    if (!newFile) return;

    setBusyFile(true);
    setError('');

    try {
      const created = await uploadFile(taskId, newFile);
      setFiles((current) => [...current, created]);
      setNewFile(null);
      event.target.reset();
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusyFile(false);
    }
  };

  if (loading) return <MainCard title="Task">Loading task...</MainCard>;

  if (!task || !options) {
    return <MainCard title="Task">{error || 'Task not found.'}</MainCard>;
  }

  const canInteract = canViewAll || isAssignee;
  const canEditTask = canEdit || canReassign;

  return (
    <MainCard title={task.title}>
      <div className="d-flex flex-wrap gap-3 align-items-center mb-4">
        <Link to={`/projects/${projectId}/tasks`}>← Back to tasks</Link>
        <Badge bg={statusVariant(task.status_name)}>{task.status_name}</Badge>
        <span className="text-muted">
          Project: {options.project.project_name}
        </span>
        {canEditTask && (
          <Button
            as={Link}
            to={`/projects/${projectId}/tasks/${taskId}/edit`}
            size="sm"
            variant="outline-primary"
          >
            Edit task
          </Button>
        )}
        <Button
          as={Link}
          to={`/projects/${projectId}/tasks/${taskId}/audit`}
          size="sm"
          variant="outline-secondary"
        >
          Audit
        </Button>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      <div className="row mb-4">
        <div className="col-md-6">
          <p>
            <strong>Description:</strong><br />
            {task.description || 'No description provided.'}
          </p>
          <p>
            <strong>Assignee:</strong><br />
            {task.assignees?.length
              ? task.assignees
                  .map((item) => `${item.first_name} ${item.last_name}`)
                  .join(', ')
              : 'Unassigned'}
          </p>
          <p><strong>Task type:</strong> {task.task_type_name}</p>
          <p><strong>Priority:</strong> {task.priority_name}</p>
        </div>
        <div className="col-md-6">
          <p><strong>Start date:</strong> {task.start_date || '—'}</p>
          <p><strong>Due date:</strong> {task.due_date || '—'}</p>
          <p><strong>Estimated hours:</strong> {task.estimated_hours || '—'}</p>
        </div>
      </div>

      <hr />
      <h5>Status</h5>

      {canChangeStatus ? (
        <Form.Select
          className="mb-4"
          style={{ maxWidth: 320 }}
          value={task.status_id}
          disabled={busyStatus}
          onChange={(event) => changeStatus(event.target.value)}
        >
          {options.task_statuses.map((item) => (
            <option key={item.status_id} value={item.status_id}>
              {item.status_name}
            </option>
          ))}
        </Form.Select>
      ) : isAssignee && canCompleteAssigned ? (
        <div className="mb-4">
          {task.status_name === 'Completed' ? (
            <span className="text-muted">
              You have marked this task Completed.
            </span>
          ) : (
            <Button
              onClick={() =>
                completedStatus
                  ? changeStatus(completedStatus.status_id)
                  : setError('Completed status is not configured.')
              }
              disabled={busyStatus}
            >
              {busyStatus ? 'Updating...' : 'Mark as Completed'}
            </Button>
          )}
          <div>
            <small className="text-muted">
              Assignees can only change their task to Completed.
            </small>
          </div>
        </div>
      ) : (
        <p className="text-muted">
          Your role does not allow task status changes.
        </p>
      )}

      {canInteract && (
        <>
          <hr />
          <h5>Comments</h5>

          {comments.length === 0 ? (
            <p className="text-muted">No comments yet.</p>
          ) : (
            <div className="mb-3">
              {comments.map((comment) => (
                <div
                  key={comment.comment_id}
                  className="border rounded p-3 mb-2"
                >
                  <div className="fw-semibold">
                    {comment.first_name} {comment.last_name}
                  </div>
                  <div>{comment.comment_text}</div>
                  <small className="text-muted">
                    {formatDateTime(comment.created_at)}
                  </small>
                </div>
              ))}
            </div>
          )}

          <Form onSubmit={submitComment} className="mb-4">
            <Form.Control
              as="textarea"
              rows={2}
              className="mb-2"
              value={commentText}
              onChange={(event) => setCommentText(event.target.value)}
              placeholder="Add a comment..."
              required
            />
            <Button
              type="submit"
              size="sm"
              disabled={busyComment || !commentText.trim()}
            >
              {busyComment ? 'Adding...' : 'Add comment'}
            </Button>
          </Form>

          <hr />
          <h5>Attachments</h5>

          {files.length === 0 ? (
            <p className="text-muted">No attachments yet.</p>
          ) : (
            <ul className="mb-3">
              {files.map((file) => (
                <li key={file.attachment_id}>
                  {file.file_name}
                  {file.file_size ? ` — ${formatFileSize(file.file_size)}` : ''}
                  {file.uploaded_by_name
                    ? ` — uploaded by ${file.uploaded_by_name}`
                    : ''}
                </li>
              ))}
            </ul>
          )}

          <Form onSubmit={submitFile} className="col-lg-7">
            <Form.Group className="mb-2">
              <Form.Label>Attach document</Form.Label>
              <Form.Control
                type="file"
                onChange={chooseFile}
                accept=".pdf,.doc,.docx,.xls,.xlsx,.csv,.txt,.png,.jpg,.jpeg"
              />
              <Form.Text>Maximum file size: 10 MB.</Form.Text>
            </Form.Group>
            <Button
              type="submit"
              size="sm"
              disabled={busyFile || !newFile}
            >
              {busyFile ? 'Uploading...' : 'Attach document'}
            </Button>
          </Form>
        </>
      )}
    </MainCard>
  );
}
