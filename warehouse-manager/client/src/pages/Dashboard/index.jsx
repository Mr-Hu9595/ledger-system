// warehouse-manager/client/src/pages/Dashboard/index.jsx
import { useState, useEffect } from 'react';
import { Card, Row, Col, Table, Typography, Button, message, Modal, Form, Input, InputNumber, Select, Space, Tag } from 'antd';
import { materialAPI, inboundAPI } from '../../services/api';
import { InboxOutlined, CheckCircleOutlined, WarningOutlined, AppstoreAddOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';

const { Title } = Typography;
const { Option } = Select;

const Dashboard = () => {
  const [stats, setStats] = useState({
    total: 0,
    pending: 0,
    stored: 0,
    lowStock: 0
  });
  const [materials, setMaterials] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedStatus, setSelectedStatus] = useState('all');
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editingRecord, setEditingRecord] = useState(null);
  const [editForm] = Form.useForm();

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const materialsRes = await materialAPI.getList({ limit: 1000 });
      const materialsData = materialsRes.data;
      setMaterials(materialsData);

      setStats({
        total: materialsData.length,
        pending: materialsData.filter(m => m.inbound_status === '待入库').length,
        stored: materialsData.filter(m => m.inbound_status === '已入库').length,
        lowStock: materialsData.filter(m => m.current_stock < m.min_stock).length
      });
    } catch (error) {
      console.error('获取数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const getFilteredMaterials = () => {
    if (selectedStatus === 'all') {
      return materials;
    }
    if (selectedStatus === 'pending') {
      return materials.filter(m => m.inbound_status === '待入库');
    }
    if (selectedStatus === 'stored') {
      return materials.filter(m => m.inbound_status === '已入库');
    }
    if (selectedStatus === 'lowStock') {
      return materials.filter(m => m.current_stock < m.min_stock);
    }
    return materials;
  };

  const getStatusTag = (status) => {
    if (status === '待入库') return <Tag color="orange">待入库</Tag>;
    if (status === '已入库') return <Tag color="green">已入库</Tag>;
    return <Tag>{status}</Tag>;
  };

  const handleDelete = async (record) => {
    try {
      await materialAPI.delete(record.id);
      message.success('删除成功');
      fetchData();
    } catch (error) {
      message.error('删除失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleEdit = (record) => {
    setEditingRecord(record);
    editForm.setFieldsValue({
      name: record.name,
      specification: record.specification,
      category: record.category,
      unit: record.unit,
      current_stock: record.current_stock,
      min_stock: record.min_stock,
      notes: record.notes
    });
    setEditModalVisible(true);
  };

  const handleEditSubmit = async () => {
    try {
      const values = await editForm.validateFields();
      await materialAPI.update(editingRecord.id, values);
      message.success('更新成功');
      setEditModalVisible(false);
      editForm.resetFields();
      fetchData();
    } catch (error) {
      message.error('更新失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  const columns = [
    { title: '物料名称', dataIndex: 'name', key: 'name', width: 200 },
    { title: '规格', dataIndex: 'specification', key: 'specification', width: 120 },
    { title: '类别', dataIndex: 'category', key: 'category', width: 100 },
    { title: '单位', dataIndex: 'unit', key: 'unit', width: 80 },
    { title: '当前库存', dataIndex: 'current_stock', key: 'current_stock', width: 100 },
    { title: '最小库存', dataIndex: 'min_stock', key: 'min_stock', width: 100 },
    {
      title: '状态',
      dataIndex: 'inbound_status',
      key: 'inbound_status',
      width: 100,
      render: (status) => getStatusTag(status)
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_, record) => (
        <>
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>
            编辑
          </Button>
          <Button type="link" danger size="small" icon={<DeleteOutlined />} onClick={() => handleDelete(record)}>
            删除
          </Button>
        </>
      )
    }
  ];

  const statCards = [
    {
      key: 'pending',
      title: '待入库',
      value: stats.pending,
      icon: <InboxOutlined style={{ fontSize: 28, color: '#fff' }} />,
      color: '#faad14',
      gradient: 'linear-gradient(135deg, #faad14 0%, #ffc53d 100%)',
      shadow: '0 4px 12px rgba(250, 173, 20, 0.3)'
    },
    {
      key: 'stored',
      title: '已入库',
      value: stats.stored,
      icon: <CheckCircleOutlined style={{ fontSize: 28, color: '#fff' }} />,
      color: '#52c41a',
      gradient: 'linear-gradient(135deg, #52c41a 0%, #73d13d 100%)',
      shadow: '0 4px 12px rgba(82, 196, 26, 0.3)'
    },
    {
      key: 'lowStock',
      title: '库存不足',
      value: stats.lowStock,
      icon: <WarningOutlined style={{ fontSize: 28, color: '#fff' }} />,
      color: '#ff4d4f',
      gradient: 'linear-gradient(135deg, #ff4d4f 0%, #ff7875 100%)',
      shadow: '0 4px 12px rgba(255, 77, 79, 0.3)'
    },
    {
      key: 'all',
      title: '全部物料',
      value: stats.total,
      icon: <AppstoreAddOutlined style={{ fontSize: 28, color: '#fff' }} />,
      color: '#1890ff',
      gradient: 'linear-gradient(135deg, #1890ff 0%, #40a9ff 100%)',
      shadow: '0 4px 12px rgba(24, 144, 255, 0.3)'
    }
  ];

  const getTitle = () => {
    const titles = {
      'pending': '待入库物料',
      'stored': '已入库物料',
      'lowStock': '库存不足物料',
      'all': '全部物料'
    };
    return titles[selectedStatus] || '物料列表';
  };

  return (
    <div>
      <Title level={3} style={{ marginBottom: 24, color: '#1f1f1f' }}>首页看板</Title>

      <Row gutter={[20, 20]} style={{ marginBottom: 24 }}>
        {statCards.map((card) => (
          <Col span={6} key={card.key}>
            <Card
              loading={loading}
              hoverable
              onClick={() => setSelectedStatus(card.key)}
              style={{
                borderRadius: 12,
                overflow: 'hidden',
                boxShadow: card.shadow,
                cursor: 'pointer',
                border: selectedStatus === card.key ? `2px solid ${card.color}` : '2px solid transparent'
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
        title={<span style={{ fontSize: 16 }}>{getTitle()}</span>}
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
          dataSource={getFilteredMaterials()}
          rowKey="id"
          pagination={{ pageSize: 10, showTotal: (total) => `共 ${total} 条` }}
          style={{ marginTop: -8 }}
        />
      </Card>

      <Modal
        title="编辑物料"
        open={editModalVisible}
        onOk={handleEditSubmit}
        onCancel={() => {
          setEditModalVisible(false);
          editForm.resetFields();
        }}
        okText="保存"
        cancelText="取消"
      >
        <Form form={editForm} layout="vertical">
          <Form.Item label="名称" name="name" rules={[{ required: true, message: '请输入名称' }]}>
            <Input placeholder="请输入名称" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="规格" name="specification">
                <Input placeholder="请输入规格" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="类别" name="category">
                <Input placeholder="请输入类别" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="单位" name="unit">
                <Input placeholder="请输入单位" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="当前库存" name="current_stock">
                <InputNumber min={0} style={{ width: '100%' }} placeholder="请输入当前库存" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="最小库存" name="min_stock">
                <InputNumber min={0} style={{ width: '100%' }} placeholder="请输入最小库存" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item label="备注" name="notes">
            <Input.TextArea rows={2} placeholder="请输入备注" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Dashboard;
