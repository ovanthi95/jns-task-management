import { lazy } from 'react';

// project-imports
import DashboardLayout from 'layout/Dashboard';
import Loadable from 'components/Loadable';

// render - kanban board
const Kanban = Loadable(lazy(() => import('views/tasks/Kanban')));

// ==============================|| KANBAN ROUTING ||============================== //

const KanbanRoutes = {
  path: '/',
  children: [
    {
      path: '/',
      element: <DashboardLayout />,
      children: [
        {
          path: 'kanban',
          element: <Kanban />
        }
      ]
    }
  ]
};

export default KanbanRoutes;