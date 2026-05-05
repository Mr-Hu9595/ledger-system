// warehouse-manager/client/src/pages/OutboundList/index.jsx
import { useState, useEffect } from 'react';
import { Table, Card, Typography } from 'antd';
import AIPanel from '../../components/AIPanel';
import { outboundAPI } from '../../services/api';

const { Title } = Typography;

const OutboundList = () => {
  const [outbounds, setOutbounds] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchOutbounds();
  }, []);

  const fetchOutbounds = async () => {
    setLoading(true);
    try {
      const res = await outboundAPI.getList({ limit: 500 });
      setOutbounds(res.data);
    } catch (error) {
      console.error('获取出库记录失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    { title: '日期', dataIndex: 'outbound_date', key: 'outbound_date', width: 120 },
    { title: '时间', dataIndex: 'outbound_time', key: 'outbound_time', width: 150, render: (text) => text ? text.substring(0, 19) : '-' },
    { title: '物料名称', dataIndex: 'ledger_name', key: 'ledger_name', render: (_, record) => record.ledger?.name || '-' },
    { title: '规格', dataIndex: 'specification', render: (_, record) => record.ledger?.specification || '-' },
    { title: '数量', dataIndex: 'quantity', key: 'quantity', width: 100 },
    { title: '单位', dataIndex: 'unit', render: (_, record) => record.ledger?.unit || '-' },
    { title: '用途', dataIndex: 'usage', key: 'usage' },
    { title: '领料人', dataIndex: 'receiver', key: 'receiver', width: 100 },
    { title: '出库人', dataIndex: 'outbound_operator', key: 'outbound_operator', width: 100 }
  ];

  return (
    <div>
      <Title level={3}>出库记录</Title>
      <AIPanel mode="outbound" onSuccess={fetchOutbounds} />
      <Card>
        <Table
          columns={columns}
          dataSource={outbounds}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10, showTotal: (total) => `共 ${total} 条` }}
        />
      </Card>
    </div>
  );
};

export default OutboundList;