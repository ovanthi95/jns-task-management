import { lazy } from 'react';

import DashboardLayout from 'layout/Dashboard';
import Loadable from 'components/Loadable';
import RequireAuth from './RequireAuth';
import RequirePermission from './RequirePermission';

const ProjectList = Loadable(lazy(() => import('views/projects/ProjectList')));
const ProjectCreate = Loadable(lazy(() => import('views/projects/ProjectCreate')));
const ProjectEdit = Loadable(lazy(() => import('views/projects/ProjectEdit')));

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
          path: 'projects',
          element: <ProjectList />
        },
        {
          path: 'projects/new',
          element: (
            <RequirePermission permissions={['create_projects']}>
              <ProjectCreate />
            </RequirePermission>
          )
        },
        {
          path: 'projects/:projectId/edit',
          element: (
            <RequirePermission permissions={['edit_projects']}>
              <ProjectEdit />
            </RequirePermission>
          )
        }
      ]
    }
  ]
};

export default ProjectsRoutes;
