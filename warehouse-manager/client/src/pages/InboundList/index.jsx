// warehouse-manager/client/src/pages/InboundList/index.jsx
import { useState, useEffect } from 'react';
import { Table, Card, Tag, Typography } from 'antd';
import { inboundAPI } from '../../services/api';

const { Title } = Typography;

const InboundList = () => {
  const [inbounds, setInbounds] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchInbounds();
  }, []);

  const fetchInbounds = async () => {
    setLoading(true);
    try {
      const res = await inboundAPI.getList({ limit: 500 });
      setInbounds(res.data);
    } catch (error) {
      console.error('获取入库记录失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    { title: '日期', dataIndex: 'inbound_date', key: 'inbound_date', width: 120 },
    { title: '时间', dataIndex: 'inbound_time', key: 'inbound_time', width: 150, render: (text) => text ? text.substring(0, 19) : '-' },
    { title: '物料名称', dataIndex: 'ledger_name', key: 'ledger_name', render: (_, record) => record.ledger?.name || '-' },
    { title: '规格', dataIndex: 'specification', render: (_, record) => record.ledger?.specification || '-' },
    { title: '数量', dataIndex: 'quantity', key: 'quantity', width: 100 },
    { title: '单位', dataIndex: 'unit', render: (_, record) => record.ledger?.unit || '-' },
    { title: '供应商', dataIndex: 'supplier', key: 'supplier', width: 150 },
    { title: '入库人', dataIndex: 'inbound_operator', key: 'inbound_operator', width: 100 },
    { title: '备注', dataIndex: 'notes', key: 'notes' }
  ];

  return (
    <div>
      <Title level={3}>入库记录</Title>
      <Card>
        <Table
          columns={columns}
          dataSource={inbounds}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10, showTotal: (total) => `共 ${total} 条` }}
        />
      </Card>
    </div>
  );
};

export default InboundList;
