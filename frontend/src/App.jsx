import { RouterProvider } from 'react-router-dom';

// project-imports
import { AuthProvider } from 'contexts/AuthContext';
import router from 'routes';

// ==============================|| APP - THEME, ROUTER, LOCAL ||============================== //

// AuthProvider sits outside RouterProvider so the signed-in user survives
// navigation: inside the router it would be remounted by any route change that
// replaced the element tree, and the boot-time GET /auth/me would run again on
// every page.

function App() {
  return (
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>
  );
}

export default App;
