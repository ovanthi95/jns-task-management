import { lazy } from 'react';

import Loadable from 'components/Loadable';
import DashboardLayout from 'layout/Dashboard';
import RequireAuth from './RequireAuth';
import RequirePermission from './RequirePermission';

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
          element: (
            <RequirePermission permissions={['manage_users']}>
              <UserList />
            </RequirePermission>
          )
        },
        {
          path: 'new',
          element: (
            <RequirePermission permissions={['manage_users']}>
              <UserCreate />
            </RequirePermission>
          )
        },
        {
          path: ':userId/edit',
          element: (
            <RequirePermission permissions={['manage_users']}>
              <UserEdit />
            </RequirePermission>
          )
        }
      ]
    }
  ]
};

export default UsersRoutes;
