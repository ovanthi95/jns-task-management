import { createBrowserRouter } from 'react-router-dom';

import AccountRoutes from './AccountRoutes';
import TasksRoutes from './TasksRoutes';
import ProjectsRoutes from './ProjectsRoutes';
import UsersRoutes from './UsersRoutes';
import ManagementRoutes from './ManagementRoutes';
import NavigationRoutes from './NavigationRoutes';
import PagesRoutes from './PagesRoutes';
import NotFound from 'views/errors/NotFound';
import BadRequest from 'views/errors/BadRequest';
import Timeout from 'views/errors/Timeout';

const router = createBrowserRouter(
  [
    {
      path: '/error/400',
      element: <BadRequest />
    },
    {
      path: '/error/timeout',
      element: <Timeout />
    },
    NavigationRoutes,
    AccountRoutes,
    TasksRoutes,
    ProjectsRoutes,
    UsersRoutes,
    ManagementRoutes,
    PagesRoutes,
    {
      path: '*',
      element: <NotFound />
    }
  ],
  {
    basename: import.meta.env.VITE_APP_BASE_NAME
  }
);

export default router;
