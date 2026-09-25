// API 07 UI - Task list
// Owner: Edward

import { Link, useParams } from 'react-router-dom';

// react-bootstrap
import Alert from 'react-bootstrap/Alert';
import Badge from 'react-bootstrap/Badge';
import Button from 'react-bootstrap/Button';
import Col from 'react-bootstrap/Col';
import Form from 'react-bootstrap/Form';
import Row from 'react-bootstrap/Row';
import Spinner from 'react-bootstrap/Spinner';
import Table from 'react-bootstrap/Table';

// project-imports
import MainCard from 'components/MainCard';
import { useTaskList } from 'logic/tasks/useTaskList';
import TaskCreate from './TaskCreate';

export default function TaskList() {
  const { projectId } = useParams();
  const { tasks, filters, loading, error, setFilter, applyFilters, clearFilters, reload } = useTaskList(projectId);

  return (
    <Row className="g-3">
      <Col xs={12}>
        <TaskCreate projectId={projectId} onCreated={reload} />
      </Col>

      <Col xs={12}>
        <MainCard
          title="Tasks"
          subheader={`Project #${projectId}`}
          secondary={loading ? <Spinner animation="border" size="sm" /> : <Badge bg="secondary">{tasks.length}</Badge>}
        >
          <Form onSubmit={applyFilters} className="mb-3">
            <Row className="g-2 align-items-end">
              <Col md={3}>
                <Form.Label>Status id</Form.Label>
                <Form.Control
                  type="number"
                  min={1}
                  value={filters.status_id}
                  onChange={(event) => setFilter('status_id', event.target.value)}
                />
              </Col>
              <Col md={3}>
                <Form.Label>Priority id</Form.Label>
                <Form.Control
                  type="number"
                  min={1}
                  value={filters.priority_id}
                  onChange={(event) => setFilter('priority_id', event.target.value)}
                />
              </Col>
              <Col md={3}>
                <Form.Label>Assignee id</Form.Label>
                <Form.Control
                  type="number"
                  min={1}
                  value={filters.assignee_id}
                  onChange={(event) => setFilter('assignee_id', event.target.value)}
                />
              </Col>
              <Col md={3}>
                <Button type="submit" className="me-2" disabled={loading}>
                  Apply
                </Button>
                <Button type="button" variant="light" onClick={clearFilters} disabled={loading}>
                  Clear
                </Button>
              </Col>
            </Row>
          </Form>

          {error && <Alert variant="danger">{error}</Alert>}

          {!error && !loading && tasks.length === 0 && <Alert variant="light">No tasks match these filters.</Alert>}

          {tasks.length > 0 && (
            <Table responsive hover className="mb-0">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Title</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>Priority</th>
                  <th>Assignees</th>
                  <th>Due</th>
                  <th className="text-end">Est. hrs</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {tasks.map((task) => (
                  <tr key={task.task_id}>
                    <td>{task.task_id}</td>
                    <td>{task.title}</td>
                    <td>{task.task_type_name}</td>
                    <td>{task.status_name}</td>
                    <td>{task.priority_name}</td>
                    <td>{assigneeNames(task.assignees)}</td>
                    <td>{task.due_date || '—'}</td>
                    <td className="text-end">{task.estimated_hours || '—'}</td>
                    <td>
                      <Link
                        to={`/projects/${projectId}/tasks/${task.task_id}/edit`}
                        className="btn btn-sm btn-outline-primary"
                      >
                        Edit
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </MainCard>
      </Col>
    </Row>
  );
}

function assigneeNames(assignees) {
  if (!assignees || assignees.length === 0) {
    return '—';
  }

  return assignees.map((person) => `${person.first_name} ${person.last_name}`).join(', ');
}
