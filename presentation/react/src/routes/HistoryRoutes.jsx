import { lazy } from 'react';

import DashboardLayout from 'layout/Dashboard';
import Loadable from 'components/Loadable';
import RequireAuth from './RequireAuth';
import RequirePermission from './RequirePermission';

const History = Loadable(lazy(() => import('views/history/History')));

const HistoryRoutes = {
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
              <History />
            </RequirePermission>
          )
        }
      ]
    }
  ]
};

export default HistoryRoutes;
