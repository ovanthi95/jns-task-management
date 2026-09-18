import { lazy } from 'react';

// project-imports
import Loadable from 'components/Loadable';
import RequireAuth from 'components/RequireAuth';
import DashboardLayout from 'layout/Dashboard';

const CreateTask = Loadable(lazy(() => import('views/tasks/CreateTask')));

// ==============================|| TASK ROUTES ||============================== //

// RequireAuth wraps the layout rather than each page, so every task route added
// later is guarded by default instead of by remembering. It is a convenience,
// not a security boundary — the API rejects unauthenticated requests itself.

const TasksRoutes = {
  path: '/',
  children: [
    {
      element: <RequireAuth />,
      children: [
        {
          path: '/',
          element: <DashboardLayout />,
          children: [
            {
              path: 'tasks',
              children: [
                {
                  path: 'create',
                  element: <CreateTask />
                }
              ]
            }
          ]
        }
      ]
    }
  ]
};

export default TasksRoutes;
