// project-imports
import chartsMaps from './charts-maps';
import formComponents from './forms';
import other from './other';
import pages from './pages';
import uiComponents from './ui-components';
import tableRoutes from './tables';
import navigation from './navigation';
import users from './users';
import management from './management';

// ==============================|| MENU ITEMS ||============================== //

const menuItems = {
  items: [navigation, users, management, uiComponents, formComponents, tableRoutes, chartsMaps, pages, other]
};

export default menuItems;
