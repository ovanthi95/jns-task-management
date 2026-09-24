// API 02 UI logic
// Owner: Manatka
//
// Page state only: loading, error, users. Fetching goes through the service.

import { useEffect, useState } from 'react';

import { getUsers } from 'services/users/userListService';

export function useUserList() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;

    getUsers()
      .then((data) => {
        if (active) setUsers(data);
      })
      .catch((err) => {
        if (active) setError(err);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  return { users, loading, error };
}