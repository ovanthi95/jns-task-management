import { lazy } from 'react';

import DashboardLayout from 'layout/Dashboard';
import Loadable from 'components/Loadable';
import RequireAuth from './RequireAuth';

const TaskListPage = Loadable(lazy(() => import('views/tasks/TaskList')));
const TaskCreatePage = Loadable(lazy(() => import('views/tasks/TaskCreate')));
const TaskEditPage = Loadable(lazy(() => import('views/tasks/TaskEdit')));
const TaskCommentsPage = Loadable(lazy(() => import('views/tasks/TaskComments')));
const TaskAuditPage = Loadable(lazy(() => import('views/tasks/TaskAudit')));

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
        { path: 'projects/:projectId/tasks', element: <TaskListPage /> },
        { path: 'projects/:projectId/tasks/new', element: <TaskCreatePage /> },
        { path: 'projects/:projectId/tasks/:taskId/edit', element: <TaskEditPage /> },
        { path: 'projects/:projectId/tasks/:taskId/comments', element: <TaskCommentsPage /> },
        { path: 'projects/:projectId/tasks/:taskId/audit', element: <TaskAuditPage /> }
      ]
    }
  ]
};

export default TasksRoutes;
