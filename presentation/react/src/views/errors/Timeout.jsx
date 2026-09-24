// Timeout UI
// Owner: Jessie

import Button from 'react-bootstrap/Button';
import MainCard from 'components/MainCard';

export default function Timeout() {
  return (
    <div className="auth-main">
      <div className="auth-wrapper v1">
        <div className="auth-form">
          <MainCard className="mb-0 shadow border-0">
            <div
              className="text-center"
              style={{
                width: '100%',
                maxWidth: '420px',
                margin: '0 auto',
                padding: '30px 20px'
              }}
            >
              <h1
                className="mb-2"
                style={{
                  fontSize: '52px',
                  fontWeight: 700,
                  color: '#1677ff'
                }}
              >
                Timeout
              </h1>

              <h3 className="mb-3">Request Timeout</h3>

              <p className="text-muted mb-4">
                The request is taking too long. Please try again.
              </p>

              <Button href="/dashboard" variant="primary">
                Back to Dashboard
              </Button>
            </div>
          </MainCard>
        </div>
      </div>
    </div>
  );
}