
import { Link } from 'react-router-dom';

// project-import
import { APP_DEFAULT_PATH } from 'config';

export const DrawerHeader = () => {
  return (
    <div className="m-header">
      <Link
        to={APP_DEFAULT_PATH}
        className="b-brand d-flex align-items-center text-decoration-none"
        aria-label="JNS Business Solutions"
      >
        <span
          className="d-flex align-items-center justify-content-center me-2"
          style={{
            width: 35,
            height: 35,
            flexShrink: 0
          }}
        >
          <img
            src="/jns-favicon.svg?v=3"
            alt=""
            width="35"
            height="35"
            style={{ display: 'block', objectFit: 'contain' }}
          />
        </span>
        <span
          className="text-white fw-semibold"
          style={{
            fontSize: 18,
            lineHeight: 1.15,
            maxWidth: 170
          }}
        >
          JNS Business Solutions
        </span>
      </Link>
    </div>
  );
};
