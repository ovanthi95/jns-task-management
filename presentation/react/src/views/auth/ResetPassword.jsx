import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
import MainCard from 'components/MainCard';
import { resetPassword } from 'services/auth/passwordService';

export default function ResetPasswordPage() {
  const { uid, token } = useParams();
  const navigate = useNavigate();
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
      const data = await resetPassword(uid, token, password, confirmPassword);
      setSuccess(data.message);
      setTimeout(() => navigate('/login', { replace: true }), 1200);
    } catch (requestError) {
      setError(requestError.message || 'Unable to reset your password.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-main">
      <div className="auth-wrapper v1">
        <div className="auth-form">
          <div className="position-relative">
            <div className="auth-bg">
              <span className="r"></span>
              <span className="r s"></span>
              <span className="r s"></span>
              <span className="r"></span>
            </div>

            <MainCard className="mb-0 shadow border-0 login-card">
              <div style={{ width: '100%', maxWidth: '420px', margin: '0 auto', padding: '12px 10px' }}>
                <div className="text-center mb-4">
                  <h3 className="mb-1 f-w-600">Set a new password</h3>
                  <p className="text-muted mb-0">
                    Choose a new password for your Worklink account.
                  </p>
                </div>

                <Form onSubmit={handleSubmit}>
                  <Form.Group className="mb-3" controlId="resetPassword">
                    <Form.Label>New password</Form.Label>
                    <Form.Control
                      type="password"
                      value={password}
                      onChange={(event) => setPassword(event.target.value)}
                      autoComplete="new-password"
                      required
                      minLength={8}
                      size="lg"
                    />
                  </Form.Group>

                  <Form.Group className="mb-3" controlId="resetPasswordConfirm">
                    <Form.Label>Confirm new password</Form.Label>
                    <Form.Control
                      type="password"
                      value={confirmPassword}
                      onChange={(event) => setConfirmPassword(event.target.value)}
                      autoComplete="new-password"
                      required
                      minLength={8}
                      size="lg"
                    />
                  </Form.Group>

                  {error && <div className="alert alert-danger" role="alert">{error}</div>}
                  {success && <div className="alert alert-success" role="alert">{success}</div>}

                  <Button type="submit" variant="primary" size="lg" className="w-100" disabled={loading}>
                    {loading ? 'Saving...' : 'Set new password'}
                  </Button>

                  <div className="text-center mt-4">
                    <Link to="/login">Back to sign in</Link>
                  </div>
                </Form>
              </div>
            </MainCard>
          </div>
        </div>
      </div>
    </div>
  );
}
