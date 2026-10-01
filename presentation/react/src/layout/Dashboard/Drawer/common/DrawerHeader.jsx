import { Link } from 'react-router-dom';

import { APP_DEFAULT_PATH } from 'config';

export const DrawerHeader = () => {
  return (
    <div className="m-header">
      <Link
        to={APP_DEFAULT_PATH}
        className="b-brand text-decoration-none"
        aria-label="JNS Business Solutions dashboard"
      >
        <div className="d-flex align-items-center gap-2">
          <div
            className="d-flex align-items-center justify-content-center rounded"
            style={{
              width: 34,
              height: 34,
              background: 'rgba(255, 255, 255, 0.14)',
              color: '#ffffff',
              fontWeight: 700,
              fontSize: 13
            }}
          >
            JNS
          </div>

          <span
            className="text-white fw-semibold"
            style={{ letterSpacing: '0.02em', fontSize: 14 }}
          >
            JNS Business Solutions
          </span>
        </div>
      </Link>
    </div>
  );
};
