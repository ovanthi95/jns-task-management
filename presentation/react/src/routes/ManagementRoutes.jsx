import { lazy } from 'react';

import Loadable from 'components/Loadable';
import DashboardLayout from 'layout/Dashboard';
import RequireAuth from './RequireAuth';
import RequirePermission from './RequirePermission';

const HistoryPage = Loadable(lazy(() => import('views/history/History')));
const RolesPermissionsPage = Loadable(
  lazy(() => import('views/users/RolesPermissions'))
);
const WorkloadPage = Loadable(lazy(() => import('views/workload/Workload')));
const WorkloadUserPage = Loadable(
  lazy(() => import('views/workload/WorkloadUser'))
);

const ManagementRoutes = {
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
          path: 'history',
          element: (
            <RequirePermission permissions={['view_history']}>
              <HistoryPage />
            </RequirePermission>
          )
        },
        {
          path: 'roles',
          element: (
            <RequirePermission permissions={['manage_roles']}>
              <RolesPermissionsPage />
            </RequirePermission>
          )
        },
        {
          path: 'workload',
          element: (
            <RequirePermission permissions={['view_workload']}>
              <WorkloadPage />
            </RequirePermission>
          )
        },
        {
          path: 'workload/users/:userId',
          element: (
            <RequirePermission permissions={['view_workload']}>
              <WorkloadUserPage />
            </RequirePermission>
          )
        }
      ]
    }
  ]
};

export default ManagementRoutes;
