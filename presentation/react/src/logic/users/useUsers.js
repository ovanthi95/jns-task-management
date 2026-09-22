import useSWR from 'swr';

// project-imports
import { getUsers } from 'services/users/userService';

// ==============================|| USE USERS (API 02) ||============================== //
//
// Wraps the service call and exposes the three states a list page needs.
// swr is already a project dependency (package.json), so no new packages.

export default function useUsers() {
  const { data, error, isLoading } = useSWR('users', getUsers);

  return {
    users: data ?? [],
    isLoading,
    error
  };
}