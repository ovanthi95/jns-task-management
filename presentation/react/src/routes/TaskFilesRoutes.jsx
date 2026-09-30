// API 10 UI route
// Owner: Manatka

import { lazy } from 'react';

// project-imports
import Loadable from 'components/Loadable';
import DashboardLayout from 'layout/Dashboard';
import RequireAuth from './RequireAuth';

// render - task files page (API 10)
const TaskFiles = Loadable(lazy(() => import('views/tasks/TaskFiles')));

const TaskFilesRoutes = {
  path: '/',
  children: [
    {
      path: 'tasks/:taskId/files',
      element: (
        <RequireAuth>
          <DashboardLayout />
        </RequireAuth>
      ),
      children: [
        {
          path: '',
          element: <TaskFiles />
        }
      ]
    }
  ]
};

export default TaskFilesRoutes;