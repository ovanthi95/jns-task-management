import { lazy } from 'react';

import DashboardLayout from 'layout/Dashboard';
import Loadable from 'components/Loadable';
import RequireAuth from './RequireAuth';

const ChangePasswordPage = Loadable(lazy(() => import('views/auth/ChangePassword')));

const AccountRoutes = {
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
          path: 'change-password',
          element: <ChangePasswordPage />
        }
      ]
    }
  ]
};

export default AccountRoutes;
