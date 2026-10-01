import { useState } from 'react';
import { Link } from 'react-router-dom';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
import MainCard from 'components/MainCard';
import { requestPasswordReset } from 'services/auth/passwordService';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setMessage('');
    setError('');
    setLoading(true);

    try {
      const data = await requestPasswordReset(email);
      setMessage(data.message);
    } catch (requestError) {
      setError(requestError.message || 'Unable to request a password reset.');
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
                  <h3 className="mb-1 f-w-600">Forgot password</h3>
                  <p className="text-muted mb-0">
                    Enter your work email and we will send you a password reset link.
                  </p>
                </div>

                <Form onSubmit={handleSubmit}>
                  <Form.Group className="mb-3" controlId="forgotPasswordEmail">
                    <Form.Label>Email address</Form.Label>
                    <Form.Control
                      type="email"
                      placeholder="Enter your work email"
                      value={email}
                      onChange={(event) => setEmail(event.target.value)}
                      autoComplete="email"
                      required
                      size="lg"
                    />
                  </Form.Group>

                  {error && <div className="alert alert-danger" role="alert">{error}</div>}
                  {message && <div className="alert alert-success" role="alert">{message}</div>}

                  <Button type="submit" variant="primary" size="lg" className="w-100" disabled={loading}>
                    {loading ? 'Sending...' : 'Send reset link'}
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
