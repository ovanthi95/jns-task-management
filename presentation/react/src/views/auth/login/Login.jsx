// #login implemented by Ovanthi- 25298714

import Button from 'react-bootstrap/Button';
import { Link } from 'react-router-dom';
import Form from 'react-bootstrap/Form';
import InputGroup from 'react-bootstrap/InputGroup';

import MainCard from 'components/MainCard';

import { useLogin } from 'logic/auth/useLogin';

export default function LoginPage() {
  const {
    email,
    password,
    showPassword,
    loading,
    error,
    success,
    setEmail,
    setPassword,
    togglePassword,
    handleSubmit
  } = useLogin();

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
              <div
                style={{
                  width: '100%',
                  maxWidth: '420px',
                  margin: '0 auto',
                  padding: '12px 10px'
                }}
              >
                <div className="text-center mb-4">
                  <div
                    className="d-inline-flex align-items-center justify-content-center rounded-circle mb-3"
                    style={{
                      width: '64px',
                      height: '64px',
                      background: '#1677ff',
                      color: '#ffffff',
                      fontWeight: 700,
                      fontSize: '20px',
                      letterSpacing: '1px'
                    }}
                  >
                    JNS
                  </div>

                  <h3 className="mb-1 f-w-600">
                    JNS Task Management
                  </h3>

                  <p className="text-muted mb-0">
                    Sign in to manage projects, tasks and team workload.
                  </p>
                </div>

                <Form onSubmit={handleSubmit}>
                  <Form.Group className="mb-3" controlId="loginEmail">
                    <Form.Label>Email address</Form.Label>

                    <Form.Control
                      type="email"
                      placeholder="Enter your email"
                      value={email}
                      onChange={(event) => setEmail(event.target.value)}
                      autoComplete="email"
                      required
                      size="lg"
                    />
                  </Form.Group>

                  <Form.Group className="mb-3" controlId="loginPassword">
                    <Form.Label>Password</Form.Label>

                    <InputGroup>
                      <Form.Control
                        type={showPassword ? 'text' : 'password'}
                        placeholder="Enter your password"
                        value={password}
                        onChange={(event) => setPassword(event.target.value)}
                        autoComplete="current-password"
                        required
                        size="lg"
                      />

                      <Button
                        type="button"
                        variant="outline-secondary"
                        onClick={togglePassword}
                      >
                        <i
                          className={
                            showPassword ? 'ti ti-eye' : 'ti ti-eye-off'
                          }
                        />
                      </Button>
                    </InputGroup>
                  </Form.Group>

                  {error && (
                    <div className="alert alert-danger" role="alert">
                      {error}
                    </div>
                  )}
                  {success && (
                    <div className="alert alert-success" role="alert">
                      {success}
                    </div>
                  )}

                  <div className="d-flex justify-content-end align-items-center mb-4">
                    <Link to="/forgot-password" className="small">
                      Forgot password?
                    </Link>
                  </div>

                  <Button
                    type="submit"
                    variant="primary"
                    size="lg"
                    className="w-100"
                    disabled={loading}
                  >
                    {loading ? 'Signing in...' : 'Sign in'}
                  </Button>

                  <div className="text-center mt-4">
                    <p className="text-muted small mb-0">
                      Access is available to authorised JNS users only.
                    </p>
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