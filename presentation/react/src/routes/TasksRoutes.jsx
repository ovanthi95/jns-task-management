import { lazy } from 'react';

// project-imports
import DashboardLayout from 'layout/Dashboard';
import Loadable from 'components/Loadable';
import RequireAuth from './RequireAuth';

// render - task pages
const TaskListPage = Loadable(lazy(() => import('views/tasks/TaskList')));
const TaskCreatePage = Loadable(lazy(() => import('views/tasks/TaskCreate')));
const TaskEditPage = Loadable(lazy(() => import('views/tasks/TaskEdit')));

// ==============================|| TASK ROUTING ||============================== //

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
