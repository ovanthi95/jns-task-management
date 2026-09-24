import { createBrowserRouter } from 'react-router-dom';

// project-imports
import ChartMapRoutes from './ChartMapRoutes';
import ComponentsRoutes from './ComponentsRoutes';
import FormsRoutes from './FormsRoutes';
import OtherRoutes from './OtherRoutes';
import PagesRoutes from './PagesRoutes';
import NavigationRoutes from './NavigationRoutes';
import TablesRoutes from './TablesRoutes';
import TasksRoutes from './TasksRoutes';
import UsersRoutes from './UsersRoutes';
import TaskFilesRoutes from './TaskFilesRoutes';

// ==============================|| ROUTING RENDER ||============================== //

const router = createBrowserRouter(
  [NavigationRoutes, ComponentsRoutes, FormsRoutes, TablesRoutes, TasksRoutes, PagesRoutes, OtherRoutes, ChartMapRoutes, UsersRoutes, TaskFilesRoutes],
  {
    basename: import.meta.env.VITE_APP_BASE_NAME
  }
);

export default router;
