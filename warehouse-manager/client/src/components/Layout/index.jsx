import { Layout, Menu } from 'antd';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';
import {
  HomeOutlined,
  InboxOutlined,
  UploadOutlined,
  FileTextOutlined,
  ToolOutlined
} from '@ant-design/icons';

const { Header, Sider, Content } = Layout;

const LayoutComponent = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    { key: '/', icon: <HomeOutlined />, label: '首页' },
    {
      key: 'materials',
      icon: <InboxOutlined />,
      label: '物料管理',
      children: [
        { key: '/materials', label: '物料列表' },
        { key: '/materials/create', label: '手动录入' }
      ]
    },
    {
      key: 'inbounds',
      icon: <UploadOutlined />,
      label: '入库管理',
      children: [
        { key: '/inbounds', label: '入库记录' }
      ]
    },
    {
      key: 'outbounds',
      icon: <FileTextOutlined />,
      label: '出库管理',
      children: [
        { key: '/outbounds', label: '出库记录' }
      ]
    },
    {
      key: 'tools',
      icon: <ToolOutlined />,
      label: '工具',
      children: [
        { key: '/tools', label: '导出/同步' }
      ]
    }
  ];

  const onMenuClick = ({ key }) => {
    navigate(key);
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ background: '#001529', padding: '0 24px', display: 'flex', alignItems: 'center' }}>
        <div style={{ color: '#fff', fontSize: 20, fontWeight: 'bold' }}>仓库管理系统</div>
      </Header>
      <Layout>
        <Sider width={200} style={{ background: '#fff' }}>
          <Menu
            mode="inline"
            selectedKeys={[location.pathname]}
            defaultOpenKeys={['materials', 'inbounds', 'outbounds', 'tools']}
            items={menuItems}
            onClick={onMenuClick}
            style={{ height: '100%', borderRight: 0 }}
          />
        </Sider>
        <Layout style={{ padding: '0 24px 24px' }}>
          <Content style={{ margin: '16px 0', minHeight: 280 }}>
            <Outlet />
          </Content>
        </Layout>
      </Layout>
    </Layout>
  );
};

export default LayoutComponent;