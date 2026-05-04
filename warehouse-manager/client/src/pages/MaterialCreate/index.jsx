// warehouse-manager/client/src/pages/MaterialCreate/index.jsx
import { useState } from 'react';
import { Form, Input, Select, InputNumber, Button, Card, message } from 'antd';
import { materialAPI } from '../../services/api';
import { useNavigate } from 'react-router-dom';

const { TextArea } = Input;
const { Option } = Select;

const MaterialCreate = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const onFinish = async (values) => {
    setLoading(true);
    try {
      await materialAPI.create({
        ...values,
        inbound_status: '待入库',
        current_stock: 0
      });
      message.success('物料创建成功');
      navigate('/materials');
    } catch (error) {
      message.error('创建失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card title="手动录入物料">
      <Form form={form} layout="vertical" onFinish={onFinish}>
        <Form.Item label="名称" name="name" rules={[{ required: true, message: '请输入名称' }]}>
          <Input placeholder="请输入物料名称" />
        </Form.Item>

        <Form.Item label="规格" name="specification">
          <Input placeholder="请输入规格" />
        </Form.Item>

        <Form.Item label="类别" name="category">
          <Select placeholder="请选择类别">
            <Option value="equipment">设备</Option>
            <Option value="material">材料</Option>
            <Option value="监测仪表">监测仪表</Option>
            <Option value="视频监控">视频监控</Option>
            <Option value="雾炮设备">雾炮设备</Option>
            <Option value="洗车机设备">洗车机设备</Option>
          </Select>
        </Form.Item>

        <Form.Item label="单位" name="unit">
          <Select placeholder="请选择单位">
            <Option value="个">个</Option>
            <Option value="套">套</Option>
            <Option value="米">米</Option>
            <Option value="吨">吨</Option>
            <Option value="项">项</Option>
            <Option value="批">批</Option>
          </Select>
        </Form.Item>

        <Form.Item label="品牌" name="brand">
          <Input placeholder="请输入品牌" />
        </Form.Item>

        <Form.Item label="最小库存" name="min_stock">
          <InputNumber min={0} style={{ width: '100%' }} placeholder="请输入最小库存" />
        </Form.Item>

        <Form.Item label="物料编码" name="material_code">
          <Input placeholder="请输入物料编码" />
        </Form.Item>

        <Form.Item label="备注" name="notes">
          <TextArea rows={3} placeholder="请输入备注" />
        </Form.Item>

        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading}>提交</Button>
          <Button style={{ marginLeft: 8 }} onClick={() => navigate('/materials')}>取消</Button>
        </Form.Item>
      </Form>
    </Card>
  );
};

export default MaterialCreate;