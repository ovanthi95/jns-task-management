// API 09 UI - Add task comment
// Owner: Ovanthi

import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import Alert from 'react-bootstrap/Alert';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';

import MainCard from 'components/MainCard';
import { createComment } from 'services/tasks/commentService';

export default function TaskComments() {
  const { projectId, taskId } = useParams();
  const [commentText, setCommentText] = useState('');
  const [created, setCreated] = useState(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const submit = async (event) => {
    event.preventDefault();

    if (!commentText.trim()) {
      setError('Comment cannot be blank.');
      return;
    }

    setSaving(true);
    setError('');

    try {
      const comment = await createComment(taskId, commentText.trim());
      setCreated(comment);
      setCommentText('');
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <MainCard title={`Task #${taskId} — Add comment`}>
      {error && <Alert variant="danger">{error}</Alert>}

      {created && (
        <Alert variant="success">
          Comment added by {created.first_name} {created.last_name}.
        </Alert>
      )}

      <Form onSubmit={submit} className="col-lg-8">
        <Form.Group className="mb-3">
          <Form.Label>Comment</Form.Label>
          <Form.Control
            as="textarea"
            rows={4}
            value={commentText}
            onChange={(event) => setCommentText(event.target.value)}
            maxLength={4000}
            required
          />
        </Form.Group>

        <Button type="submit" disabled={saving || !commentText.trim()}>
          {saving ? 'Adding...' : 'Add comment'}
        </Button>

        {projectId && (
          <Link
            to={`/projects/${projectId}/tasks`}
            className="btn btn-link ms-2"
          >
            Back to tasks
          </Link>
        )}
      </Form>
    </MainCard>
  );
}
