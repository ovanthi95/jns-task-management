import { lazy } from 'react';

import DashboardLayout from 'layout/Dashboard';
import Loadable from 'components/Loadable';
import RequireAuth from './RequireAuth';

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
        { path: 'workload', element: <Workload /> },
        { path: 'workload/users/:userId', element: <WorkloadUser /> }
      ]
    }
  ]
};

export default WorkloadRoutes;
