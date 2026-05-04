import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import MaterialList from './pages/MaterialList';
import MaterialCreate from './pages/MaterialCreate';
import InboundList from './pages/InboundList';
import OutboundList from './pages/OutboundList';
import Tools from './pages/Tools';

const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    children: [
      { index: true, element: <Dashboard /> },
      { path: 'materials', element: <MaterialList /> },
      { path: 'materials/create', element: <MaterialCreate /> },
      { path: 'inbounds', element: <InboundList /> },
      { path: 'outbounds', element: <OutboundList /> },
      { path: 'tools', element: <Tools /> }
    ]
  }
]);

export default router;