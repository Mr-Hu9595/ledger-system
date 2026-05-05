import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import MaterialList from './pages/MaterialList';
import MaterialCreate from './pages/MaterialCreate';
import InboundList from './pages/InboundList';
import OutboundList from './pages/OutboundList';
import Tools from './pages/Tools';
import EncodingList from './pages/EncodingList';
import EncodingMaintain from './pages/EncodingMaintain';

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
      { path: 'tools', element: <Tools /> },
      { path: 'encoding', element: <EncodingList /> },
      { path: 'encoding/maintain', element: <EncodingMaintain /> }
    ]
  }
]);

export default router;