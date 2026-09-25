import { lazy } from 'react';

import Loadable from 'components/Loadable';
import DashboardLayout from 'layout/Dashboard';
import RequireAuth from './RequireAuth';

const UserList = Loadable(lazy(() => import('views/users/UserList')));
const UserCreate = Loadable(lazy(() => import('views/users/UserCreate')));
const UserEdit = Loadable(lazy(() => import('views/users/UserEdit')));

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
        },
        {
          path: ':userId/edit',
          element: <UserEdit />
        }
      ]
    }
  ]
};

export default UsersRoutes;
