// warehouse-manager/client/src/pages/Dashboard/index.jsx
import { useState, useEffect } from 'react';
import { Card, Row, Col, Table, Tag, Typography, Statistic } from 'antd';
import { materialAPI, inboundAPI } from '../../services/api';
import { ArrowUpOutlined, InboxOutlined, CheckCircleOutlined, WarningOutlined, AppstoreAddOutlined } from '@ant-design/icons';

const { Title } = Typography;

const Dashboard = () => {
  const [stats, setStats] = useState({
    total: 0,
    pending: 0,
    stored: 0,
    lowStock: 0
  });
  const [recentInbounds, setRecentInbounds] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const materialsRes = await materialAPI.getList({ limit: 1000 });
      const materials = materialsRes.data;

      setStats({
        total: materials.length,
        pending: materials.filter(m => m.inbound_status === '待入库').length,
        stored: materials.filter(m => m.inbound_status === '已入库').length,
        lowStock: materials.filter(m => m.current_stock < m.min_stock).length
      });

      const inboundsRes = await inboundAPI.getList({ limit: 5 });
      setRecentInbounds(inboundsRes.data);
    } catch (error) {
      console.error('获取数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    { title: '日期', dataIndex: 'inbound_date', key: 'inbound_date' },
    { title: '物料名称', dataIndex: 'ledger_name', key: 'ledger_name', render: (text, record) => record.ledger?.name || '-' },
    { title: '数量', dataIndex: 'quantity', key: 'quantity' },
    { title: '供应商', dataIndex: 'supplier', key: 'supplier' }
  ];

  const statCards = [
    {
      title: '待入库',
      value: stats.pending,
      icon: <InboxOutlined style={{ fontSize: 28, color: '#fff' }} />,
      color: '#faad14',
      gradient: 'linear-gradient(135deg, #faad14 0%, #ffc53d 100%)',
      shadow: '0 4px 12px rgba(250, 173, 20, 0.3)'
    },
    {
      title: '已入库',
      value: stats.stored,
      icon: <CheckCircleOutlined style={{ fontSize: 28, color: '#fff' }} />,
      color: '#52c41a',
      gradient: 'linear-gradient(135deg, #52c41a 0%, #73d13d 100%)',
      shadow: '0 4px 12px rgba(82, 196, 26, 0.3)'
    },
    {
      title: '库存不足',
      value: stats.lowStock,
      icon: <WarningOutlined style={{ fontSize: 28, color: '#fff' }} />,
      color: '#ff4d4f',
      gradient: 'linear-gradient(135deg, #ff4d4f 0%, #ff7875 100%)',
      shadow: '0 4px 12px rgba(255, 77, 79, 0.3)'
    },
    {
      title: '全部物料',
      value: stats.total,
      icon: <AppstoreAddOutlined style={{ fontSize: 28, color: '#fff' }} />,
      color: '#1890ff',
      gradient: 'linear-gradient(135deg, #1890ff 0%, #40a9ff 100%)',
      shadow: '0 4px 12px rgba(24, 144, 255, 0.3)'
    }
  ];

  return (
    <div>
      <Title level={3} style={{ marginBottom: 24, color: '#1f1f1f' }}>首页看板</Title>

      <Row gutter={[20, 20]} style={{ marginBottom: 24 }}>
        {statCards.map((card, index) => (
          <Col span={6} key={index}>
            <Card
              loading={loading}
              style={{
                borderRadius: 12,
                overflow: 'hidden',
                boxShadow: card.shadow
              }}
              styles={{
                header: {
                  background: card.gradient,
                  color: '#fff',
                  border: 'none',
                  padding: '12px 20px'
                },
                body: { padding: '20px 20px 24px' }
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <div style={{ color: '#8c8c8c', fontSize: 14, marginBottom: 8 }}>{card.title}</div>
                  <div style={{ fontSize: 36, fontWeight: 'bold', color: card.color, lineHeight: 1 }}>{card.value}</div>
                </div>
                <div style={{
                  width: 48,
                  height: 48,
                  borderRadius: 8,
                  background: card.gradient,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  {card.icon}
                </div>
              </div>
            </Card>
          </Col>
        ))}
      </Row>

      <Card
        title={<span style={{ fontSize: 16 }}>最近入库记录</span>}
        loading={loading}
        style={{ borderRadius: 12 }}
        styles={{
          header: {
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            color: '#fff',
            border: 'none',
            borderRadius: '12px 12px 0 0'
          },
          body: { padding: '20px' }
        }}
      >
        <Table
          columns={columns}
          dataSource={recentInbounds}
          rowKey="id"
          pagination={false}
          style={{ marginTop: -8 }}
        />
      </Card>
    </div>
  );
};

export default Dashboard;
