import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
import MainCard from 'components/MainCard';
import { changePassword } from 'services/auth/passwordService';

export default function ChangePasswordPage() {
  const navigate = useNavigate();
  const [currentPassword, setCurrentPassword] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setSuccess('');

    if (password.length < 8) {
      setError('Password must be at least 8 characters.');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setLoading(true);

    try {
      const data = await changePassword(currentPassword, password, confirmPassword);
      setSuccess(data.message);
      setTimeout(() => navigate('/login', { replace: true }), 1200);
    } catch (requestError) {
      setError(requestError.message || 'Unable to change your password.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <MainCard title="Change password">
      <div style={{ maxWidth: '520px' }}>
        <p className="text-muted">
          Change your Worklink password. You will be signed out after a successful change.
        </p>

        <Form onSubmit={handleSubmit}>
          <Form.Group className="mb-3" controlId="currentPassword">
            <Form.Label>Current password</Form.Label>
            <Form.Control
              type="password"
              value={currentPassword}
              onChange={(event) => setCurrentPassword(event.target.value)}
              autoComplete="current-password"
              required
            />
          </Form.Group>

          <Form.Group className="mb-3" controlId="newPassword">
            <Form.Label>New password</Form.Label>
            <Form.Control
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="new-password"
              required
              minLength={8}
            />
          </Form.Group>

          <Form.Group className="mb-4" controlId="confirmPassword">
            <Form.Label>Confirm new password</Form.Label>
            <Form.Control
              type="password"
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              autoComplete="new-password"
              required
              minLength={8}
            />
          </Form.Group>

          {error && <div className="alert alert-danger" role="alert">{error}</div>}
          {success && <div className="alert alert-success" role="alert">{success}</div>}

          <Button type="submit" variant="primary" disabled={loading}>
            {loading ? 'Saving...' : 'Change password'}
          </Button>
        </Form>
      </div>
    </MainCard>
  );
}
