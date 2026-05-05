// warehouse-manager/client/src/pages/MaterialCreate/index.jsx
import { useState } from 'react';
import { Form, Input, Select, InputNumber, Button, Card, message, Row, Col, Divider, Tag, Space } from 'antd';
import { materialAPI, encodingAPI } from '../../services/api';
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

  // 智能提取文本中的关键信息
  const extractFromText = () => {
    if (!rawText.trim()) {
      message.warning('请输入要解析的文本');
      return;
    }

    const text = rawText.trim();
    const extracted = {};

    // 提取名称（第一个字符到第一个数量词或特殊字符）
    const namePatterns = [
      /名称[：:]\s*(.+?)(?=\s*[规数品材供]|$)/i,
      /品名[：:]\s*(.+?)(?=\s*[规数供]|$)/i,
      /(.+?)(?=\s*[规数材供]|$)/,
    ];
    for (const pattern of namePatterns) {
      const match = text.match(pattern);
      if (match && match[1]) {
        extracted.name = match[1].trim();
        break;
      }
    }

    // 提取规格
    const specPatterns = [
      /规格[：:]\s*(.+?)(?=\s*[数材供]|型号|$)/i,
      /规格型号[：:]\s*(.+?)(?=\s*[数材供]|$)/i,
      /型号[：:]\s*(.+?)(?=\s*[数材供]|$)/i,
    ];
    for (const pattern of specPatterns) {
      const match = text.match(pattern);
      if (match && match[1]) {
        extracted.specification = match[1].trim();
        break;
      }
    }

    // 提取数量
    const qtyPatterns = [
      /数量[：:]\s*(\d+(?:\.\d+)?)\s*(?:个|套|米|吨|项|批)?/i,
      /(\d+(?:\.\d+)?)\s*(?:个|套|米|吨|项|批)/,
    ];
    for (const pattern of qtyPatterns) {
      const match = text.match(pattern);
      if (match && match[1]) {
        extracted.quantity = parseFloat(match[1]);
        // 提取单位
        const unitMatch = text.match(/(?:个|套|米|吨|项|批)/);
        if (unitMatch) {
          extracted.unit = unitMatch[0];
        }
        break;
      }
    }

    // 提取品牌
    const brandPatterns = [
      /品牌[：:]\s*(.+?)(?=\s*[材供]|$)/i,
      /厂家[：:]\s*(.+?)(?=\s*[材供]|$)/i,
    ];
    for (const pattern of brandPatterns) {
      const match = text.match(pattern);
      if (match && match[1]) {
        extracted.brand = match[1].trim();
        break;
      }
    }

    // 提取材质
    const materialPatterns = [
      /材质[：:]\s*(.+?)(?=\s*[供]|$)/i,
    ];
    for (const pattern of materialPatterns) {
      const match = text.match(pattern);
      if (match && match[1]) {
        extracted.material_type = match[1].trim();
        break;
      }
    }

    // 提取公称直径
    const diameterPatterns = [
      /DN(\d+)/i,
      /直径[：:]\s*DN?(\d+)/i,
    ];
    for (const pattern of diameterPatterns) {
      const match = text.match(pattern);
      if (match && match[1]) {
        extracted.nominal_diameter = 'DN' + match[1];
        break;
      }
    }

    // 提取压力
    const pressurePatterns = [
      /压力[：:]\s*(\d+(?:\.\d+)?)\s*(?:MPa|帕)?/i,
      /(\d+(?:\.\d+)?)\s*MPa/i,
    ];
    for (const pattern of pressurePatterns) {
      const match = text.match(pattern);
      if (match && match[1]) {
        extracted.pressure = match[1] + 'MPa';
        break;
      }
    }

    // 如果没提取到名称，尝试直接取整段文字作为名称
    if (!extracted.name && text.length < 100) {
      extracted.name = text;
    }

    // 更新表单
    if (Object.keys(extracted).length > 0) {
      form.setFieldsValue(extracted);
      const keys = Object.keys(extracted).join('、');
      message.success(`已提取: ${keys}`);
    } else {
      message.warning('未能识别关键信息，请手动填写');
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
        <Card
          title={<><RobotOutlined style={{ color: '#52c41a' }} /> AI智能解析</>}
          style={{ borderRadius: 12, height: '100%' }}
          styles={{ header: { background: 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)', color: '#fff' } }}
        >
          <div style={{ marginBottom: 16 }}>
            <p style={{ color: '#666', fontSize: 13 }}>
              输入物料描述文本，AI将自动提取关键信息。例如：
            </p>
            <div style={{ background: '#f5f5f5', padding: 12, borderRadius: 8, fontSize: 12, color: '#888' }}>
              <div>名称：球阀-1</div>
              <div>规格：Q47F-10-DN150</div>
              <div>品牌：杭州阀门厂</div>
              <div>数量：10个</div>
            </div>
          </div>

          <TextArea
            rows={6}
            placeholder="粘贴物料描述文本，系统将自动提取：名称、规格、数量、单位、品牌等信息..."
            value={rawText}
            onChange={(e) => setRawText(e.target.value)}
            style={{ marginBottom: 16 }}
          />

          <Button
            type="primary"
            icon={<RobotOutlined />}
            onClick={extractFromText}
            block
            size="large"
            style={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              border: 'none',
              borderRadius: 8,
              height: 48
            }}
          >
            智能提取信息
          </Button>

          <Button
            type="default"
            icon={<SyncOutlined spin={codeGenerating} />}
            onClick={handleSmartMatchCode}
            loading={codeGenerating}
            block
            size="large"
            style={{
              marginTop: 12,
              borderRadius: 8,
              height: 48
            }}
          >
            智能匹配编码
          </Button>

          <Divider style={{ margin: '20px 0 16px' }}>
            <Tag color="blue">支持的提取字段</Tag>
          </Divider>

          <Row gutter={[8, 8]}>
            {['名称', '规格', '数量', '单位', '品牌', '材质', '公称直径', '压力'].map(field => (
              <Col key={field}>
                <Tag color="cyan" style={{ borderRadius: 12 }}>{field}</Tag>
              </Col>
            ))}
          </Row>
        </Card>
      </Col>
    </Row>
  );
};

export default MaterialCreate;
