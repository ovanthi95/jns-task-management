import { lazy } from 'react';
import { Navigate } from 'react-router-dom';

import Loadable from 'components/Loadable';
import AuthLayout from 'layout/Auth';

const LoginPage = Loadable(lazy(() => import('views/auth/login/Login')));
const ForgotPasswordPage = Loadable(lazy(() => import('views/auth/ForgotPassword')));
const ResetPasswordPage = Loadable(lazy(() => import('views/auth/ResetPassword')));

const PagesRoutes = {
  path: '/',
  children: [
    {
      path: '/',
      element: <AuthLayout />,
      children: [
        {
          index: true,
          element: <Navigate to="/login" replace />
        },
        {
          path: 'login',
          element: <LoginPage />
        },
        {
          path: 'forgot-password',
          element: <ForgotPasswordPage />
        },
        {
          path: 'reset-password/:uid/:token',
          element: <ResetPasswordPage />
        }
      ]
    }
  ]
};

export default PagesRoutes;
