import { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';

import { getSessionUser } from 'services/auth/sessionService';

export default function RequireRole({ roles, children }) {
  const [status, setStatus] = useState('checking');

  useEffect(() => {
    let active = true;

    getSessionUser()
      .then((user) => {
        if (!active) return;

        if (!user) {
          setStatus('unauthenticated');
          return;
        }

        const allowed = roles.some(
          (role) =>
            role.toLowerCase() ===
            String(user.role_name || '').toLowerCase()
        );

        setStatus(allowed ? 'allowed' : 'denied');
      })
      .catch(() => {
        if (active) setStatus('unauthenticated');
      });

    return () => {
      active = false;
    };
  }, [roles]);

  if (status === 'checking') {
    return <div className="text-center py-5">Checking access...</div>;
  }

  if (status === 'unauthenticated') {
    return <Navigate to="/login" replace />;
  }

  if (status === 'denied') {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
}
