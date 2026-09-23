import { lazy } from 'react';

// project-imports
import Loadable from 'components/Loadable';
import DashboardLayout from 'layout/Dashboard';
import RequireAuth from './RequireAuth';

// render - dashboard pages
const DefaultPages = Loadable(
  lazy(() => import('views/navigation/dashboard/Default'))
);

const NavigationRoutes = {
  path: '/',
  children: [
    {
      path: 'dashboard',
      element: (
        <RequireAuth>
          <DashboardLayout />
        </RequireAuth>
      ),
      children: [
        {
          path: '',
          element: <DefaultPages />
        }
      ]
    }
  ]
};

export default NavigationRoutes;