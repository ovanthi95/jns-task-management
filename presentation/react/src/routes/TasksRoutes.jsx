import { lazy } from 'react';

import DashboardLayout from 'layout/Dashboard';
import Loadable from 'components/Loadable';
import RequireAuth from './RequireAuth';

const TaskListPage = Loadable(lazy(() => import('views/tasks/TaskList')));
const TaskCreatePage = Loadable(lazy(() => import('views/tasks/TaskCreate')));
const TaskEditPage = Loadable(lazy(() => import('views/tasks/TaskEdit')));

const TasksRoutes = {
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
          path: 'projects/:projectId/tasks',
          element: <TaskListPage />
        },
        {
          path: 'projects/:projectId/tasks/new',
          element: <TaskCreatePage />
        },
        {
          path: 'projects/:projectId/tasks/:taskId/edit',
          element: <TaskEditPage />
        }
      ]
    }
  ]
};

export default TasksRoutes;
