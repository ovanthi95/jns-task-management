import { lazy } from 'react';

// project-imports
import DashboardLayout from 'layout/Dashboard';
import Loadable from 'components/Loadable';

// render - task pages (API 06 and API 07)
const TaskListPage = Loadable(lazy(() => import('views/tasks/TaskList')));
const TaskCreatePage = Loadable(lazy(() => import('views/tasks/TaskCreate')));

// ==============================|| TASK ROUTING ||============================== //
//
// The browser paths mirror the API paths, so /projects/1/tasks in the address
// bar is the page for /api/projects/1/tasks. The project id is a route
// parameter for the same reason it is a URL segment on the API: a task
// belongs to exactly one project and the page cannot be asked for without it.
//
// The list page already renders the create form, so /tasks/new exists only
// for linking straight to it.

const TasksRoutes = {
  path: '/',
  children: [
    {
      path: '/',
      element: <DashboardLayout />,
      children: [
        {
          path: 'projects/:projectId/tasks',
          element: <TaskListPage />
        },
        {
          path: 'projects/:projectId/tasks/new',
          element: <TaskCreatePage />
        }
      ]
    }
  ]
};

export default TasksRoutes;
