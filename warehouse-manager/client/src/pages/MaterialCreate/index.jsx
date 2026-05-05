// warehouse-manager/client/src/pages/MaterialCreate/index.jsx
import { useState } from 'react';
import { Form, Input, Select, InputNumber, Button, Card, message, Row, Col, Divider, Tag, Space } from 'antd';
import { materialAPI, encodingAPI } from '../../services/api';
import AIPanel from '../../components/AIPanel';
import { useNavigate } from 'react-router-dom';
import { RobotOutlined, ThunderboltOutlined, SyncOutlined } from '@ant-design/icons';

const { TextArea } = Input;
const { Option } = Select;

const MaterialCreate = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [codeGenerating, setCodeGenerating] = useState(false);
  const [rawText, setRawText] = useState('');
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

  // AI识别后填充表单
  const handleAIFill = (data) => {
    const formData = {};
    if (data.name) formData.name = data.name;
    if (data.specification) formData.specification = data.specification;
    if (data.category) formData.category = data.category;
    if (data.unit) formData.unit = data.unit;
    if (data.brand) formData.brand = data.brand;
    if (data.nominal_diameter) formData.nominal_diameter = data.nominal_diameter;
    if (data.pressure) formData.pressure = data.pressure;
    if (data.min_stock) formData.min_stock = parseFloat(data.min_stock);
    if (data.notes) formData.notes = data.notes;

    form.setFieldsValue(formData);
    message.success('AI识别结果已填充到表单');
  };

  // 自动生成物料编码
  const handleAutoGenerateCode = async () => {
    try {
      const values = form.getFieldsValue();
      const { category, unit } = values;

      if (!category) {
        message.warning('请先选择类别');
        return;
      }

      setCodeGenerating(true);

      // 获取类别编码
      const categoryCodeMap = {
        'equipment': '01',
        'material': '02',
        '监测仪表': '03',
        '视频监控': '04',
        '雾炮设备': '05',
        '洗车机设备': '06'
      };

      // 获取单位编码
      const unitCodeMap = {
        '个': '01',
        '套': '02',
        '米': '03',
        '吨': '04',
        '项': '05',
        '批': '06'
      };

      const category_code = categoryCodeMap[category] || '01';
      const supplier_code = '01'; // 默认供应商编码
      const year = new Date().getFullYear().toString();

      const response = await encodingAPI.generateCode({
        category_code,
        supplier_code,
        year
      });

      if (response.code) {
        form.setFieldsValue({ material_code: response.code });
        message.success('编码生成成功');
      }
    } catch (error) {
      console.error('生成编码失败:', error);
      message.error('生成编码失败，请重试');
    } finally {
      setCodeGenerating(false);
    }
  };

  // 智能匹配物料编码
  const handleSmartMatchCode = async () => {
    try {
      const values = form.getFieldsValue();
      const { name, specification } = values;

      if (!name && !specification) {
        message.warning('请先填写名称或规格');
        return;
      }

      setCodeGenerating(true);

      const searchText = [name, specification].filter(Boolean).join(' ');
      const response = await encodingAPI.matchKeyword(searchText);

      if (response.suggested_code) {
        form.setFieldsValue({ material_code: response.suggested_code });
        message.success('智能匹配成功');
      } else if (response.matched_rule) {
        form.setFieldsValue({ material_code: response.matched_rule.code });
        message.success('已匹配相似规则');
      } else {
        message.info('未找到匹配规则，请手动输入编码');
      }
    } catch (error) {
      console.error('匹配编码失败:', error);
      message.error('匹配编码失败，请重试');
    } finally {
      setCodeGenerating(false);
    }
  };

  return (
    <Row gutter={24}>
      <Col span={14}>
        <Card
          title={<><ThunderboltOutlined style={{ color: '#1890ff' }} /> 手动录入物料</>}
          style={{ borderRadius: 12 }}
          styles={{ header: { background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: '#fff' } }}
        >
          <Form form={form} layout="vertical" onFinish={onFinish}>
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item label="名称" name="name" rules={[{ required: true, message: '请输入名称' }]}>
                  <Input placeholder="请输入物料名称" size="large" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="规格" name="specification">
                  <Input placeholder="请输入规格" size="large" />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={8}>
                <Form.Item label="类别" name="category">
                  <Select placeholder="请选择类别" size="large">
                    <Option value="equipment">设备</Option>
                    <Option value="material">材料</Option>
                    <Option value="监测仪表">监测仪表</Option>
                    <Option value="视频监控">视频监控</Option>
                    <Option value="雾炮设备">雾炮设备</Option>
                    <Option value="洗车机设备">洗车机设备</Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item label="单位" name="unit">
                  <Select placeholder="请选择单位" size="large">
                    <Option value="个">个</Option>
                    <Option value="套">套</Option>
                    <Option value="米">米</Option>
                    <Option value="吨">吨</Option>
                    <Option value="项">项</Option>
                    <Option value="批">批</Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item label="品牌" name="brand">
                  <Input placeholder="请输入品牌" size="large" />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={8}>
                <Form.Item label="公称直径" name="nominal_diameter">
                  <Input placeholder="如 DN50" size="large" />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item label="压力" name="pressure">
                  <Input placeholder="如 1.6MPa" size="large" />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item label="最小库存" name="min_stock">
                  <InputNumber min={0} style={{ width: '100%' }} placeholder="请输入" size="large" />
                </Form.Item>
              </Col>
            </Row>

            <Form.Item label="物料编码" name="material_code">
              <Input
                placeholder="请输入或自动生成物料编码"
                size="large"
                suffix={
                  <Space size={4}>
                    <Button
                      size="small"
                      icon={<SyncOutlined />}
                      loading={codeGenerating}
                      onClick={handleAutoGenerateCode}
                    >
                      自动生成
                    </Button>
                  </Space>
                }
              />
            </Form.Item>

            <Form.Item label="备注" name="notes">
              <TextArea rows={2} placeholder="请输入备注" />
            </Form.Item>

            <Form.Item>
              <Button type="primary" htmlType="submit" loading={loading} size="large" block>
                提交物料
              </Button>
            </Form.Item>
          </Form>
        </Card>
      </Col>

      <Col span={10}>
        <AIPanel
          mode="material"
          fillOnly={true}
          onFill={handleAIFill}
        />
      </Col>
    </Row>
  );
};

export default MaterialCreate;