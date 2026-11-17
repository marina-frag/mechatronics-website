import '@fontsource-variable/inter';
import './styles/global.css';

import { StrictMode, lazy } from 'react';
import { createRoot } from 'react-dom/client';
import { RouterProvider, createBrowserRouter } from 'react-router';
import { App } from './App';
import { ErrorPage } from './pages/ErrorPage';
import { HomePage } from './pages/HomePage';
import { MaterialPage } from './pages/MaterialPage';
import { NotFoundPage } from './pages/NotFoundPage';

// Η σελίδα του Spot κουβαλά το three.js: φορτώνεται μόνο όταν τη χρειαστούμε.
const SpotPage = lazy(() => import('./pages/spot/SpotPage'));

const router = createBrowserRouter(
  [
    {
      path: '/',
      element: <App />,
      errorElement: <ErrorPage />,
      children: [
        {
          // Σφάλμα σε μια σελίδα: εμφανίζεται μέσα στο layout, με το μενού διαθέσιμο.
          errorElement: <ErrorPage />,
          children: [
            { index: true, element: <HomePage /> },
            { path: 'projects/spot', element: <SpotPage /> },
            { path: 'material', element: <MaterialPage /> },
            { path: '*', element: <NotFoundPage /> },
          ],
        },
      ],
    },
  ],
  { basename: import.meta.env.BASE_URL.replace(/\/$/, '') || '/' },
);

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>,
);
