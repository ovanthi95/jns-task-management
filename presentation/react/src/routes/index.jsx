import { createBrowserRouter } from 'react-router-dom';

// project-imports
import ChartMapRoutes from './ChartMapRoutes';
import ComponentsRoutes from './ComponentsRoutes';
import FormsRoutes from './FormsRoutes';
import OtherRoutes from './OtherRoutes';
import PagesRoutes from './PagesRoutes';
import NavigationRoutes from './NavigationRoutes';
import TablesRoutes from './TablesRoutes';
import NotFound from 'views/errors/NotFound';
import BadRequest from 'views/errors/BadRequest';
import Timeout from 'views/errors/Timeout';

// ==============================|| ROUTING RENDER ||============================== //

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
    {
      path: '*',
      element: <NotFound />
    },
    NavigationRoutes,
    ComponentsRoutes,
    FormsRoutes,
    TablesRoutes,
    PagesRoutes,
    OtherRoutes,
    ChartMapRoutes
  ],
    {
    basename: import.meta.env.VITE_APP_BASE_NAME
  }
);

export default router;
