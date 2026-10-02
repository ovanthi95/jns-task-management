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
            borderRadius: 10,
            background: 'linear-gradient(135deg, #1DE9B6, #1DC4E9)',
            flexShrink: 0
          }}
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 20 20"
            fill="none"
            aria-hidden="true"
          >
            <path
              d="M17 5L10.5 11.5L7 8L2 13"
              stroke="white"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d="M13 5H17V9"
              stroke="white"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
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
