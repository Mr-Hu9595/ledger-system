// warehouse-manager/client/src/pages/InboundList/index.jsx
import { useState, useEffect } from 'react';
import { Table, Card, Typography, Form, Input, InputNumber, Select, Button, Row, Col, message, Modal } from 'antd';
import { inboundAPI, materialAPI } from '../../services/api';
import AIPanel from '../../components/AIPanel';
import { ThunderboltOutlined, EditOutlined } from '@ant-design/icons';

const { Title } = Typography;
const { Option } = Select;

const InboundList = () => {
  const [inbounds, setInbounds] = useState([]);
  const [materials, setMaterials] = useState([]);
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();
  const [submitLoading, setSubmitLoading] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editingRecord, setEditingRecord] = useState(null);
  const [editForm] = Form.useForm();

  useEffect(() => {
    fetchInbounds();
    fetchMaterials();
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

  const fetchMaterials = async () => {
    try {
      const res = await materialAPI.getList({ limit: 1000 });
      setMaterials(res.data);
    } catch (error) {
      console.error('获取物料列表失败:', error);
    }
  };

  const handleManualSubmit = async (values) => {
    setSubmitLoading(true);
    try {
      await inboundAPI.create({
        ...values,
        inbound_date: values.inbound_date || new Date().toISOString().split('T')[0]
      });
      message.success('入库记录创建成功');
      form.resetFields();
      fetchInbounds();
    } catch (error) {
      message.error('创建失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setSubmitLoading(false);
    }
  };

  const handleDelete = async (record) => {
    try {
      await inboundAPI.delete(record.id);
      message.success('删除成功');
      fetchInbounds();
    } catch (error) {
      message.error('删除失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleEdit = (record) => {
    setEditingRecord(record);
    editForm.setFieldsValue({
      ledger_id: record.ledger_id,
      quantity: record.quantity,
      inbound_date: record.inbound_date,
      supplier: record.supplier,
      inbound_operator: record.inbound_operator,
      notes: record.notes
    });
    setEditModalVisible(true);
  };

  const handleEditSubmit = async () => {
    try {
      const values = await editForm.validateFields();
      await inboundAPI.update(editingRecord.id, values);
      message.success('更新成功');
      setEditModalVisible(false);
      editForm.resetFields();
      fetchInbounds();
    } catch (error) {
      message.error('更新失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  const columns = [
    { title: '日期', dataIndex: 'inbound_date', key: 'inbound_date', width: 120 },
    { title: '时间', dataIndex: 'inbound_time', key: 'inbound_time', width: 100, render: (text) => text ? (typeof text === 'string' ? text.substring(0, 8) : text) : '-' },
    { title: '物料名称', dataIndex: 'ledger_name', key: 'ledger_name', render: (_, record) => record.ledger?.name || '-' },
    { title: '规格', dataIndex: 'specification', render: (_, record) => record.ledger?.specification || '-' },
    { title: '数量', dataIndex: 'quantity', key: 'quantity', width: 100 },
    { title: '单位', dataIndex: 'unit', render: (_, record) => record.ledger?.unit || '-' },
    { title: '供应商', dataIndex: 'supplier', key: 'supplier', width: 150 },
    { title: '入库人', dataIndex: 'inbound_operator', key: 'inbound_operator', width: 100 },
    { title: '备注', dataIndex: 'notes', key: 'notes' },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_, record) => (
        <>
          <Button type="link" icon={<EditOutlined />} onClick={() => handleEdit(record)}>
            编辑
          </Button>
          <Button type="link" danger onClick={() => handleDelete(record)}>
            删除
          </Button>
        </>
      )
    }
  ];

  return (
    <div>
      <Title level={3}>入库记录</Title>

      <Row gutter={24} style={{ marginBottom: 24 }}>
        {/* 左侧：手动录入 */}
        <Col span={12}>
          <Card
            title={<><ThunderboltOutlined style={{ color: '#1890ff' }} /> 手动录入</>}
            style={{ borderRadius: 12 }}
            styles={{ header: { background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: '#fff' } }}
          >
            <Form form={form} layout="vertical" onFinish={handleManualSubmit}>
              <Row gutter={16}>
                <Col span={24}>
                  <Form.Item
                    label="物料"
                    name="ledger_id"
                    rules={[{ required: true, message: '请选择物料' }]}
                  >
                    <Select placeholder="请选择物料" size="large" showSearch filterOption={(input, option) =>
                      option.children.props.children[1].props.children.toLowerCase().includes(input.toLowerCase())
                    }>
                      {materials.map(m => (
                        <Option key={m.id} value={m.id}>
                          {m.name} {m.specification ? `(${m.specification})` : ''}
                        </Option>
                      ))}
                    </Select>
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    label="数量"
                    name="quantity"
                    rules={[{ required: true, message: '请输入数量' }]}
                  >
                    <InputNumber min={0} style={{ width: '100%' }} placeholder="请输入数量" size="large" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="入库日期"
                    name="inbound_date"
                    rules={[{ required: true, message: '请输入日期' }]}
                    extra="格式: 2026-05-05"
                  >
                    <Input placeholder="2026-05-05" size="large" />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item label="供应商" name="supplier">
                    <Input placeholder="请输入供应商" size="large" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item label="入库人" name="inbound_operator">
                    <Input placeholder="请输入入库人" size="large" />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item label="备注" name="notes">
                <Input.TextArea rows={2} placeholder="请输入备注" />
              </Form.Item>

              <Form.Item>
                <Button type="primary" htmlType="submit" loading={submitLoading} size="large" block>
                  提交入库
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </Col>

        {/* 右侧：AI录入 */}
        <Col span={12}>
          <AIPanel mode="inbound" onSuccess={fetchInbounds} />
        </Col>
      </Row>

      <Card>
        <Table
          columns={columns}
          dataSource={inbounds}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10, showTotal: (total) => `共 ${total} 条` }}
        />
      </Card>

      <Modal
        title="编辑入库记录"
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
          <Form.Item
            label="物料"
            name="ledger_id"
            rules={[{ required: true, message: '请选择物料' }]}
          >
            <Select placeholder="请选择物料" showSearch filterOption={(input, option) =>
              option.children.props.children[1].props.children.toLowerCase().includes(input.toLowerCase())
            }>
              {materials.map(m => (
                <Option key={m.id} value={m.id}>
                  {m.name} {m.specification ? `(${m.specification})` : ''}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="数量"
                name="quantity"
                rules={[{ required: true, message: '请输入数量' }]}
              >
                <InputNumber min={0} style={{ width: '100%' }} placeholder="请输入数量" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="入库日期"
                name="inbound_date"
                rules={[{ required: true, message: '请输入日期' }]}
              >
                <Input placeholder="2026-05-05" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="供应商" name="supplier">
                <Input placeholder="请输入供应商" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="入库人" name="inbound_operator">
                <Input placeholder="请输入入库人" />
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

export default InboundList;