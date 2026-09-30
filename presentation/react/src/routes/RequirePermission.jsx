import { useEffect, useMemo, useState } from 'react';
import { Navigate } from 'react-router-dom';

import { getSessionUser } from 'services/auth/sessionService';

export default function RequirePermission({ permissions, any = false, children }) {
  const [status, setStatus] = useState('checking');

  const required = useMemo(
    () => permissions || [],
    [permissions]
  );

  useEffect(() => {
    let active = true;

    getSessionUser()
      .then((user) => {
        if (!active) return;

        if (!user) {
          setStatus('unauthenticated');
          return;
        }

        const granted = new Set(user.permissions || []);
        const allowed = any
          ? required.some((permission) => granted.has(permission))
          : required.every((permission) => granted.has(permission));

        setStatus(allowed ? 'allowed' : 'denied');
      })
      .catch(() => {
        if (active) setStatus('unauthenticated');
      });

    return () => {
      active = false;
    };
  }, [required, any]);

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
