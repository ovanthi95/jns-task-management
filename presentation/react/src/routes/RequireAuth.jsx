import { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';

import { getSessionUser } from 'services/auth/sessionService';


export default function RequireAuth({ children }) {
  const [authStatus, setAuthStatus] = useState('checking');

  useEffect(() => {
    let active = true;

    const checkSession = async () => {
      try {
        const user = await getSessionUser();

        if (!active) {
          return;
        }

        if (user) {
          setAuthStatus('authenticated');
        } else {
          setAuthStatus('unauthenticated');
        }
      } catch {
        if (active) {
          setAuthStatus('unauthenticated');
        }
      }
    };

    checkSession();

    return () => {
      active = false;
    };
  }, []);

  if (authStatus === 'checking') {
    return <div className="text-center py-5">Checking session...</div>;
  }

  if (authStatus === 'unauthenticated') {
    return <Navigate to="/login" replace />;
  }

  return children;
}