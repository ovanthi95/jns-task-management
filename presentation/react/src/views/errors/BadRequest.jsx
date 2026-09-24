// 400 / Bad Request UI
// Owner: Jessie

import Button from 'react-bootstrap/Button';
import MainCard from 'components/MainCard';

export default function BadRequest() {
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
                  fontSize: '72px',
                  fontWeight: 700,
                  color: '#1677ff'
                }}
              >
                400
              </h1>

              <h3 className="mb-3">Bad Request</h3>

              <p className="text-muted mb-4">
                The request could not be processed. Please check your information and try again.
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