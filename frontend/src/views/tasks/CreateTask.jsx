import { useState } from 'react';

import Button from 'react-bootstrap/Button';
import Col from 'react-bootstrap/Col';
import Form from 'react-bootstrap/Form';
import Row from 'react-bootstrap/Row';

import MainCard from 'components/MainCard';

export default function CreateTask() {
  const [validated, setValidated] = useState(false);

  const handleSubmit = (event) => {
    const form = event.currentTarget;

    event.preventDefault();

    if (form.checkValidity() === false) {
      event.stopPropagation();
    } else {
      alert('Task form works. Backend connection will be added later.');
    }

    setValidated(true);
  };

  return (
    <MainCard title="Create Task">
      <Form noValidate validated={validated} onSubmit={handleSubmit}>
        <Row>
          <Form.Group as={Col} md="6" className="mb-3">
            <Form.Label>Task Title</Form.Label>
            <Form.Control required type="text" placeholder="Enter task title" />
            <Form.Control.Feedback type="invalid">Please enter a task title.</Form.Control.Feedback>
          </Form.Group>

          <Form.Group as={Col} md="6" className="mb-3">
            <Form.Label>Project</Form.Label>
            <Form.Select required defaultValue="">
              <option value="" disabled>
                Select project
              </option>
              <option>Project 1</option>
              <option>Project 2</option>
            </Form.Select>
          </Form.Group>
        </Row>

        <Form.Group className="mb-3">
          <Form.Label>Description</Form.Label>
          <Form.Control as="textarea" rows={4} placeholder="Enter task description" />
        </Form.Group>

        <Row>
          <Form.Group as={Col} md="6" className="mb-3">
            <Form.Label>Assignee</Form.Label>
            <Form.Select required defaultValue="">
              <option value="" disabled>
                Select assignee
              </option>
              <option>Unassigned</option>
            </Form.Select>
          </Form.Group>

          <Form.Group as={Col} md="3" className="mb-3">
            <Form.Label>Priority</Form.Label>
            <Form.Select required defaultValue="">
              <option value="" disabled>
                Select priority
              </option>
              <option>Low</option>
              <option>Medium</option>
              <option>High</option>
            </Form.Select>
          </Form.Group>

          <Form.Group as={Col} md="3" className="mb-3">
            <Form.Label>Status</Form.Label>
            <Form.Select required defaultValue="To Do">
              <option>To Do</option>
              <option>In Progress</option>
              <option>Review</option>
              <option>Done</option>
            </Form.Select>
          </Form.Group>
        </Row>

        <Form.Group className="mb-3">
          <Form.Label>Due Date</Form.Label>
          <Form.Control required type="date" />
        </Form.Group>

        <Button type="submit">Create Task</Button>
      </Form>
    </MainCard>
  );
}
