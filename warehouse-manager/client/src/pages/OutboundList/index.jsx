// warehouse-manager/client/src/pages/OutboundList/index.jsx
import { useState, useEffect } from 'react';
import { Table, Card, Typography, Form, Input, InputNumber, Select, Button, Row, Col, message } from 'antd';
import { outboundAPI, materialAPI } from '../../services/api';
import AIPanel from '../../components/AIPanel';
import { ThunderboltOutlined } from '@ant-design/icons';

const { Title } = Typography;
const { Option } = Select;

const OutboundList = () => {
  const [outbounds, setOutbounds] = useState([]);
  const [materials, setMaterials] = useState([]);
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();
  const [submitLoading, setSubmitLoading] = useState(false);

  useEffect(() => {
    fetchOutbounds();
    fetchMaterials();
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
      await outboundAPI.create({
        ...values,
        outbound_date: values.outbound_date || new Date().toISOString().split('T')[0]
      });
      message.success('出库记录创建成功');
      form.resetFields();
      fetchOutbounds();
    } catch (error) {
      message.error('创建失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setSubmitLoading(false);
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
                    label="出库日期"
                    name="outbound_date"
                    rules={[{ required: true, message: '请输入日期' }]}
                    extra="格式: 2026-05-05"
                  >
                    <Input placeholder="2026-05-05" size="large" />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item label="用途" name="usage">
                    <Input placeholder="请输入用途" size="large" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item label="领料人" name="receiver">
                    <Input placeholder="请输入领料人" size="large" />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={24}>
                  <Form.Item label="出库人" name="outbound_operator">
                    <Input placeholder="请输入出库人" size="large" />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item label="备注" name="notes">
                <Input.TextArea rows={2} placeholder="请输入备注" />
              </Form.Item>

              <Form.Item>
                <Button type="primary" htmlType="submit" loading={submitLoading} size="large" block>
                  提交出库
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </Col>

        {/* 右侧：AI录入 */}
        <Col span={12}>
          <AIPanel mode="outbound" onSuccess={fetchOutbounds} />
        </Col>
      </Row>

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