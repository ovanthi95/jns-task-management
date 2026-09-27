import { lazy } from 'react';

import DashboardLayout from 'layout/Dashboard';
import Loadable from 'components/Loadable';
import RequireAuth from './RequireAuth';

const ProjectCreate = Loadable(lazy(() => import('views/projects/ProjectCreate')));

const ProjectsRoutes = {
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
          path: 'projects/new',
          element: <ProjectCreate />
        }
      ]
    }
  ]
};

export default ProjectsRoutes;
