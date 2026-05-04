// warehouse-manager/client/src/pages/Dashboard/index.jsx
import { useState, useEffect } from 'react';
import { Card, Row, Col, Table, Tag, Typography } from 'antd';
import { materialAPI, inboundAPI } from '../../services/api';

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
      // 获取所有物料
      const materialsRes = await materialAPI.getList({ limit: 1000 });
      const materials = materialsRes.data;

      // 计算统计数据
      setStats({
        total: materials.length,
        pending: materials.filter(m => m.inbound_status === '待入库').length,
        stored: materials.filter(m => m.inbound_status === '已入库').length,
        lowStock: materials.filter(m => m.current_stock < m.min_stock).length
      });

      // 获取最近入库记录
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

  return (
    <div>
      <Title level={3}>首页看板</Title>

      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card title="待入库" loading={loading}>
            <div style={{ fontSize: 32, textAlign: 'center', color: '#faad14' }}>{stats.pending}</div>
          </Card>
        </Col>
        <Col span={6}>
          <Card title="已入库" loading={loading}>
            <div style={{ fontSize: 32, textAlign: 'center', color: '#52c41a' }}>{stats.stored}</div>
          </Card>
        </Col>
        <Col span={6}>
          <Card title="库存不足" loading={loading}>
            <div style={{ fontSize: 32, textAlign: 'center', color: '#ff4d4f' }}>{stats.lowStock}</div>
          </Card>
        </Col>
        <Col span={6}>
          <Card title="全部物料" loading={loading}>
            <div style={{ fontSize: 32, textAlign: 'center', color: '#1890ff' }}>{stats.total}</div>
          </Card>
        </Col>
      </Row>

      {/* 最近入库记录 */}
      <Card title="最近入库记录" loading={loading}>
        <Table
          columns={columns}
          dataSource={recentInbounds}
          rowKey="id"
          pagination={false}
        />
      </Card>
    </div>
  );
};

export default Dashboard;