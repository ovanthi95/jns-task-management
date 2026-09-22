import { lazy } from 'react';

// project-imports
import DashboardLayout from 'layout/Dashboard';
import Loadable from 'components/Loadable';

// render - users pages
const UserList = Loadable(lazy(() => import('views/users/UserList')));
const UserCreate = Loadable(lazy(() => import('views/users/UserCreate')));

// ==============================|| USERS ROUTING (API 02 / API 03) ||============================== //

const UsersRoutes = {
  path: '/',
  children: [
    {
      path: '/',
      element: <DashboardLayout />,
      children: [
        {
          path: 'users',
          element: <UserList />
        },
        {
          path: 'users/new',
          element: <UserCreate />
        }
      ]
    }
  ]
};

export default UsersRoutes;