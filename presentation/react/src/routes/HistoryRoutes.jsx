import { lazy } from 'react';

import DashboardLayout from 'layout/Dashboard';
import Loadable from 'components/Loadable';
import RequireAuth from './RequireAuth';

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
          element: <History />
        }
      ]
    }
  ]
};

export default HistoryRoutes;
