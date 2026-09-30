import { lazy } from 'react';

import DashboardLayout from 'layout/Dashboard';
import Loadable from 'components/Loadable';
import RequireAuth from './RequireAuth';
import RequirePermission from './RequirePermission';

const Workload = Loadable(lazy(() => import('views/workload/Workload')));
const WorkloadUser = Loadable(lazy(() => import('views/workload/WorkloadUser')));

const WorkloadRoutes = {
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
          path: 'workload',
          element: (
            <RequirePermission permissions={['view_workload']}>
              <Workload />
            </RequirePermission>
          )
        },
        {
          path: 'workload/users/:userId',
          element: (
            <RequirePermission permissions={['view_workload']}>
              <WorkloadUser />
            </RequirePermission>
          )
        }
      ]
    }
  ]
};

export default WorkloadRoutes;
