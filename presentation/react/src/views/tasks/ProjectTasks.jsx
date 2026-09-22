import { useNavigate, useParams, Link } from 'react-router-dom';

// react-bootstrap
import Alert from 'react-bootstrap/Alert';
import Badge from 'react-bootstrap/Badge';
import Button from 'react-bootstrap/Button';
import Col from 'react-bootstrap/Col';
import Form from 'react-bootstrap/Form';
import Row from 'react-bootstrap/Row';
import Spinner from 'react-bootstrap/Spinner';
import Stack from 'react-bootstrap/Stack';
import Table from 'react-bootstrap/Table';

// project-imports
import MainCard from 'components/MainCard';
import useProjectTasks from 'logic/tasks/useProjectTasks';
import { formatDate, formatHours, priorityVariant, statusVariant } from './taskDisplay';

// ==============================|| TASKS - PROJECT TASK LIST (API 07) ||============================== //

export default function ProjectTasks() {
  // The route may or may not carry the project. /tasks lands here with nothing
  // and falls back to the user's first project; the selector then puts the id
  // in the URL so the page can be linked to and reloaded.
  const { projectId: projectIdParam } = useParams();
  const navigate = useNavigate();

  const { projects, projectId, changeProject, lookups, members, tasks, filters, hasFilters, changeFilter, clearFilters, loading, error } =
    useProjectTasks(projectIdParam ? Number(projectIdParam) : undefined);

  const handleProjectChange = (value) => {
    changeProject(value);
    if (value) navigate(`/projects/${value}/tasks`);
  };

  return (
    <MainCard
      title="Tasks"
      subheader="Tasks in the selected project"
      secondary={
        <Button as={Link} to={projectId ? `/projects/${projectId}/tasks/new` : '#'} disabled={!projectId} size="sm">
          <i className="ph ph-plus me-1" />
          New task
        </Button>
      }
    >
      <Row className="mb-3 g-2">
        <Form.Group as={Col} md={3} controlId="taskFilterProject">
          <Form.Label className="small text-muted">Project</Form.Label>
          <Form.Select value={projectId ?? ''} onChange={(event) => handleProjectChange(event.target.value)}>
            {projects.map((project) => (
              <option key={project.project_id} value={project.project_id}>
                {project.project_name}
              </option>
            ))}
          </Form.Select>
        </Form.Group>

        <Form.Group as={Col} md={3} controlId="taskFilterStatus">
          <Form.Label className="small text-muted">Status</Form.Label>
          <Form.Select value={filters.status_id} onChange={(event) => changeFilter('status_id', event.target.value)}>
            <option value="">All statuses</option>
            {lookups.statuses.map((status) => (
              <option key={status.status_id} value={status.status_id}>
                {status.status_name}
              </option>
            ))}
          </Form.Select>
        </Form.Group>

        <Form.Group as={Col} md={3} controlId="taskFilterPriority">
          <Form.Label className="small text-muted">Priority</Form.Label>
          <Form.Select value={filters.priority_id} onChange={(event) => changeFilter('priority_id', event.target.value)}>
            <option value="">All priorities</option>
            {lookups.priorities.map((priority) => (
              <option key={priority.priority_id} value={priority.priority_id}>
                {priority.priority_name}
              </option>
            ))}
          </Form.Select>
        </Form.Group>

        <Form.Group as={Col} md={3} controlId="taskFilterAssignee">
          <Form.Label className="small text-muted">Assignee</Form.Label>
          <Form.Select value={filters.assignee_id} onChange={(event) => changeFilter('assignee_id', event.target.value)}>
            <option value="">Anyone</option>
            {members.map((member) => (
              <option key={member.user_id} value={member.user_id}>
                {member.first_name} {member.last_name}
              </option>
            ))}
          </Form.Select>
        </Form.Group>
      </Row>

      {hasFilters && (
        <Stack direction="horizontal" className="mb-3">
          <Button variant="link" size="sm" className="p-0" onClick={clearFilters}>
            Clear filters
          </Button>
        </Stack>
      )}

      {error && <Alert variant="danger">{error}</Alert>}

      <Table responsive hover className="mb-0">
        <thead>
          <tr>
            <th>Title</th>
            <th>Type</th>
            <th>Status</th>
            <th>Priority</th>
            <th>Assigned to</th>
            <th>Due</th>
            <th className="text-end">Hours</th>
          </tr>
        </thead>
        <tbody>
          {loading && (
            <tr>
              <td colSpan={7} className="text-center py-4">
                <Spinner animation="border" size="sm" className="me-2" />
                Loading tasks
              </td>
            </tr>
          )}

          {!loading && tasks.length === 0 && !error && (
            <tr>
              <td colSpan={7} className="text-center text-muted py-4">
                {/* A filter that matches nothing is a normal result, not an
                    error, so it says which case this is rather than leaving the
                    user to guess the project is empty. */}
                {hasFilters ? 'No tasks match these filters.' : 'This project has no tasks yet.'}
              </td>
            </tr>
          )}

          {!loading &&
            tasks.map((task) => (
              <tr key={task.task_id}>
                <td>
                  <div className="fw-medium">{task.title}</div>
                  {task.description && <small className="text-muted">{task.description}</small>}
                </td>
                <td>{task.task_type_name}</td>
                <td>
                  <Badge bg={statusVariant(task.status_id)}>{task.status_name}</Badge>
                </td>
                <td>
                  <Badge bg={priorityVariant(task.priority_id)}>{task.priority_name}</Badge>
                </td>
                <td>
                  {/* task_assignees allows several rows per task even though
                      API 06 creates one, so this renders a list rather than a
                      single name. */}
                  {task.assignees.length === 0 ? (
                    <span className="text-muted">Unassigned</span>
                  ) : (
                    task.assignees.map((assignee) => (
                      <div key={assignee.user_id}>
                        {assignee.first_name} {assignee.last_name}
                        {assignee.assignment_role && <small className="text-muted"> ({assignee.assignment_role})</small>}
                      </div>
                    ))
                  )}
                </td>
                <td>{formatDate(task.due_date)}</td>
                <td className="text-end">
                  {formatHours(task.actual_hours)} / {formatHours(task.estimated_hours)}
                </td>
              </tr>
            ))}
        </tbody>
      </Table>
    </MainCard>
  );
}
