import { lazy } from 'react';
import { Navigate } from 'react-router-dom';

// project-imports
import Loadable from 'components/Loadable';
import AuthLayout from 'layout/Auth';

// render - login pages
const LoginPage = Loadable(lazy(() => import('views/auth/login/Login')));

// render - register pages
const RegisterPage = Loadable(lazy(() => import('views/auth/register/Register')));

// ==============================|| AUTH PAGES ROUTING ||============================== //

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
          path: 'register',
          element: <RegisterPage />
        }
      ]
    }
  ]
};

export default PagesRoutes;
