import { lazy } from 'react';

import DashboardLayout from 'layout/Dashboard';
import Loadable from 'components/Loadable';
import RequireAuth from './RequireAuth';
import RequirePermission from './RequirePermission';

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
          element: (
            <RequirePermission permissions={['manage_roles']}>
              <RoleManagement />
            </RequirePermission>
          )
        }
      ]
    }
  ]
};

export default RoleRoutes;
