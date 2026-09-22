// react-bootstrap
import Alert from 'react-bootstrap/Alert';
import Badge from 'react-bootstrap/Badge';
import Card from 'react-bootstrap/Card';
import Col from 'react-bootstrap/Col';
import Row from 'react-bootstrap/Row';
import Spinner from 'react-bootstrap/Spinner';

// project-imports
import MainCard from 'components/MainCard';
import useKanban from 'logic/tasks/useKanban';
import useKanbanData from 'logic/tasks/useKanbanData';

// ==============================|| TASKS - KANBAN BOARD (API 07 consumer) ||============================== //
//
// Read-only board. Moving a card needs PATCH /api/tasks/:taskId (API 08,
// Ovanthi), so there is no drag-and-drop here by design.
// Data comes from useKanbanData, the single place that will switch from mock
// to Edward's useProjectTasks hook once his branch is on main.

const PRIORITY_VARIANT = { Low: 'secondary', Medium: 'info', High: 'warning', Urgent: 'danger' };

export default function Kanban() {
  const { tasks, loading, error, projectName } = useKanbanData();
  const { columns, unmapped } = useKanban(tasks);

  let body;

  if (loading) {
    body = (
      <div className="text-center py-5">
        <Spinner animation="border" size="sm" className="me-2" />
        Loading board...
      </div>
    );
  } else if (error) {
    body = <Alert variant="danger" className="mb-0">Could not load tasks. Please try again.</Alert>;
  } else if (tasks.length === 0) {
    body = <p className="text-muted text-center py-5 mb-0">This project has no tasks yet.</p>;
  } else {
    body = (
      <Row className="g-3">
        {columns.map((column) => (
          <Col key={column.key} md={6} xl={3}>
            <div className="d-flex justify-content-between align-items-center mb-2">
              <h6 className="mb-0">{column.title}</h6>
              <Badge bg="light" text="dark">{column.tasks.length}</Badge>
            </div>
            {column.tasks.length === 0 && <p className="small text-muted">Nothing here</p>}
            {column.tasks.map((task) => (
              <Card key={task.task_id} className="mb-2 shadow-none border">
                <Card.Body className="p-2">
                  <div className="fw-medium">{task.title}</div>
                  <div className="d-flex justify-content-between align-items-center mt-2">
                    <Badge bg={PRIORITY_VARIANT[task.priority_name] ?? 'secondary'}>{task.priority_name}</Badge>
                    <small className="text-muted">{task.due_date ?? ''}</small>
                  </div>
                  <small className="text-muted d-block mt-1">
                    {task.assignees.length === 0
                      ? 'Unassigned'
                      : task.assignees.map((a) => `${a.first_name} ${a.last_name}`).join(', ')}
                  </small>
                </Card.Body>
              </Card>
            ))}
          </Col>
        ))}
      </Row>
    );
  }

  return (
    <MainCard title="Kanban" subheader={<p className="mb-0">{projectName ? `Project: ${projectName}` : 'Tasks by stage'}</p>}>
      {unmapped.length > 0 && (
        <Alert variant="warning">{unmapped.length} task(s) have a status not on this board.</Alert>
      )}
      {body}
    </MainCard>
  );
}