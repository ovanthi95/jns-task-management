import { lazy } from 'react';

// project-imports
import DashboardLayout from 'layout/Dashboard';
import Loadable from 'components/Loadable';

// The paths mirror the REST routes the pages call, so a URL in the browser and
// a URL in the API contract read the same way:
//
//   /projects/:projectId/tasks       ->  API 07  GET  /api/projects/:projectId/tasks
//   /projects/:projectId/tasks/new   ->  API 06  POST /api/projects/:projectId/tasks
//
// /tasks exists because the sidebar needs a link that does not hard-code a
// project id. It renders the same list page with no project in the URL; the
// page falls back to the user's first project and then puts that id in the URL.

const ProjectTasks = Loadable(lazy(() => import('views/tasks/ProjectTasks')));
const TaskCreate = Loadable(lazy(() => import('views/tasks/TaskCreate')));

// ==============================|| TASKS ROUTING ||============================== //

const TasksRoutes = {
  path: '/',
  children: [
    {
      path: '/',
      element: <DashboardLayout />,
      children: [
        {
          path: 'tasks',
          element: <ProjectTasks />
        },
        {
          path: 'projects/:projectId/tasks',
          children: [
            {
              path: '',
              element: <ProjectTasks />
            },
            {
              path: 'new',
              element: <TaskCreate />
            }
          ]
        }
      ]
    }
  ]
};

export default TasksRoutes;
