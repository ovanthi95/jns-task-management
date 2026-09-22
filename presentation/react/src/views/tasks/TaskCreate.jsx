import { useNavigate, useParams, Link } from 'react-router-dom';

// react-bootstrap
import Alert from 'react-bootstrap/Alert';
import Button from 'react-bootstrap/Button';
import Col from 'react-bootstrap/Col';
import Form from 'react-bootstrap/Form';
import Row from 'react-bootstrap/Row';
import Spinner from 'react-bootstrap/Spinner';
import Stack from 'react-bootstrap/Stack';

// project-imports
import MainCard from 'components/MainCard';
import useTaskForm from 'logic/tasks/useTaskForm';

// ==============================|| TASKS - CREATE TASK (API 06) ||============================== //

export default function TaskCreate() {
  const { projectId } = useParams();
  const navigate = useNavigate();

  const { values, change, lookups, members, project, validated, submitting, error, dateOrderError, submit } = useTaskForm(projectId, {
    // Back to the list, so the new row is visible straight away rather than
    // the user being left on a cleared form wondering whether it saved.
    onCreated: () => navigate(`/projects/${projectId}/tasks`)
  });

  const field = (name) => ({
    value: values[name],
    onChange: (event) => change(name, event.target.value)
  });

  return (
    <MainCard
      title="New task"
      subheader={project ? `Adding to ${project.project_name}` : 'Adding to this project'}
      secondary={
        <Button as={Link} to={`/projects/${projectId}/tasks`} variant="light" size="sm">
          Back to tasks
        </Button>
      }
    >
      {error && <Alert variant="danger">{error}</Alert>}

      <Form noValidate validated={validated} onSubmit={submit}>
        <Row>
          <Form.Group as={Col} md={12} className="mb-3" controlId="taskTitle">
            <Form.Label>Title</Form.Label>
            {/* maxLength matches tasks.title varchar(200). Letting the user
                type past it here only to be rejected by the endpoint is a
                round trip that never needed to happen. */}
            <Form.Control required type="text" maxLength={200} placeholder="What needs doing" {...field('title')} />
            <Form.Control.Feedback type="invalid">A title is required.</Form.Control.Feedback>
          </Form.Group>
        </Row>

        <Row>
          <Form.Group as={Col} md={12} className="mb-3" controlId="taskDescription">
            <Form.Label>
              Description <small className="text-muted">(optional)</small>
            </Form.Label>
            <Form.Control as="textarea" rows={3} placeholder="Any detail the assignee will need" {...field('description')} />
          </Form.Group>
        </Row>

        <Row>
          <Form.Group as={Col} md={4} className="mb-3" controlId="taskType">
            <Form.Label>Task type</Form.Label>
            <Form.Select required {...field('task_type_id')}>
              <option value="">Choose a type</option>
              {lookups.task_types.map((type) => (
                <option key={type.task_type_id} value={type.task_type_id}>
                  {type.type_name}
                </option>
              ))}
            </Form.Select>
            <Form.Control.Feedback type="invalid">Choose a task type.</Form.Control.Feedback>
          </Form.Group>

          <Form.Group as={Col} md={4} className="mb-3" controlId="taskStatus">
            <Form.Label>Status</Form.Label>
            <Form.Select required {...field('status_id')}>
              {lookups.statuses.map((status) => (
                <option key={status.status_id} value={status.status_id}>
                  {status.status_name}
                </option>
              ))}
            </Form.Select>
            <Form.Control.Feedback type="invalid">Choose a status.</Form.Control.Feedback>
          </Form.Group>

          <Form.Group as={Col} md={4} className="mb-3" controlId="taskPriority">
            <Form.Label>Priority</Form.Label>
            <Form.Select required {...field('priority_id')}>
              <option value="">Choose a priority</option>
              {lookups.priorities.map((priority) => (
                <option key={priority.priority_id} value={priority.priority_id}>
                  {priority.priority_name}
                </option>
              ))}
            </Form.Select>
            <Form.Control.Feedback type="invalid">Choose a priority.</Form.Control.Feedback>
          </Form.Group>
        </Row>

        <Row>
          <Form.Group as={Col} md={4} className="mb-3" controlId="taskAssignee">
            <Form.Label>Assign to</Form.Label>
            {/* Only members of this project. The endpoint rejects anyone else,
                so offering the whole organisation here would produce a 400 the
                user could not have predicted. */}
            <Form.Select required {...field('assignee_id')}>
              <option value="">Choose a member</option>
              {members.map((member) => (
                <option key={member.user_id} value={member.user_id}>
                  {member.first_name} {member.last_name}
                </option>
              ))}
            </Form.Select>
            <Form.Control.Feedback type="invalid">Choose who this is assigned to.</Form.Control.Feedback>
            {members.length === 0 && <Form.Text className="text-muted">This project has no members to assign to yet.</Form.Text>}
          </Form.Group>

          <Form.Group as={Col} md={4} className="mb-3" controlId="taskStartDate">
            <Form.Label>
              Start date <small className="text-muted">(optional)</small>
            </Form.Label>
            <Form.Control type="date" {...field('start_date')} />
          </Form.Group>

          <Form.Group as={Col} md={4} className="mb-3" controlId="taskDueDate">
            <Form.Label>
              Due date <small className="text-muted">(optional)</small>
            </Form.Label>
            <Form.Control type="date" isInvalid={Boolean(dateOrderError)} {...field('due_date')} />
            {/* Two fields compared against each other, which the browser's own
                validation cannot do, so this message is driven from state. */}
            <Form.Control.Feedback type="invalid">{dateOrderError}</Form.Control.Feedback>
          </Form.Group>
        </Row>

        <Row>
          <Form.Group as={Col} md={4} className="mb-3" controlId="taskEstimatedHours">
            <Form.Label>
              Estimated hours <small className="text-muted">(optional)</small>
            </Form.Label>
            {/* decimal(6,2) in the schema: four digits before the point, two
                after. step allows the halves people actually enter. */}
            <Form.Control type="number" min="0" max="9999.99" step="0.25" placeholder="0.00" {...field('estimated_hours')} />
            <Form.Control.Feedback type="invalid">Enter hours as a number, or leave it blank.</Form.Control.Feedback>
          </Form.Group>
        </Row>

        <Stack direction="horizontal" gap={2}>
          <Button type="submit" disabled={submitting}>
            {submitting && <Spinner animation="border" size="sm" className="me-2" />}
            Create task
          </Button>
          <Button as={Link} to={`/projects/${projectId}/tasks`} variant="light">
            Cancel
          </Button>
        </Stack>
      </Form>
    </MainCard>
  );
}
