import { lazy } from 'react';

import DashboardLayout from 'layout/Dashboard';
import Loadable from 'components/Loadable';
import RequireAuth from './RequireAuth';

const RoleManagement = Loadable(
  lazy(() => import('views/users/RoleManagement'))
);

const RoleRoutes = {
  path: '/',
  children: [
    {
      path: '/',
      element: (
        <RequireAuth>
          <DashboardLayout />
        </RequireAuth>
      ),
      children: [
        {
          path: 'roles',
          element: <RoleManagement />
        }
      ]
    }
  ]
};

export default RoleRoutes;
