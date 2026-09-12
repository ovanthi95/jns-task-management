import { lazy } from 'react';

import Loadable from 'components/Loadable';
import DashboardLayout from 'layout/Dashboard';

const CreateTask = Loadable(lazy(() => import('views/tasks/CreateTask')));

const TasksRoutes = {
  path: '/',
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
};

export default TasksRoutes;
