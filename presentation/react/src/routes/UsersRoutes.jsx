import { lazy } from 'react';

// project-imports
import Loadable from 'components/Loadable';
import DashboardLayout from 'layout/Dashboard';
import RequireAuth from './RequireAuth';

// render - users pages (API 02 / API 03)
const UserList = Loadable(lazy(() => import('views/users/UserList')));
const UserCreate = Loadable(lazy(() => import('views/users/UserCreate')));

const UsersRoutes = {
  path: '/',
  children: [
    {
      path: 'users',
      element: (
        <RequireAuth>
          <DashboardLayout />
        </RequireAuth>
      ),
      children: [
        {
          path: '',
          element: <UserList />
        },
        {
          path: 'new',
          element: <UserCreate />
        }
      ]
    }
  ]
};

export default UsersRoutes;