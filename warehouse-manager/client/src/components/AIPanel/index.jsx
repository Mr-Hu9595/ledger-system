import { useState } from 'react';
import { Card, Input, Button, Upload, Space, message, Spin, Alert } from 'antd';
import { RobotOutlined, CameraOutlined, FileOutlined, UploadOutlined } from '@ant-design/icons';
import { aiAPI } from '../../services/api';
import './styles.css';

const { TextArea } = Input;

// 根据mode定义表单字段
const MODE_FIELDS = {
  inbound: [
    { key: 'ledger_name', label: '物料名称', required: true },
    { key: 'quantity', label: '数量', required: true },
    { key: 'unit', label: '单位' },
    { key: 'supplier', label: '供应商' },
    { key: 'inbound_date', label: '入库日期' },
    { key: 'notes', label: '备注' }
  ],
  outbound: [
    { key: 'ledger_name', label: '物料名称', required: true },
    { key: 'quantity', label: '数量', required: true },
    { key: 'unit', label: '单位' },
    { key: 'usage', label: '用途' },
    { key: 'receiver', label: '领料人' },
    { key: 'outbound_date', label: '出库日期' },
    { key: 'notes', label: '备注' }
  ],
  material: [
    { key: 'name', label: '名称', required: true },
    { key: 'specification', label: '规格' },
    { key: 'category', label: '类别' },
    { key: 'unit', label: '单位' },
    { key: 'brand', label: '品牌' },
    { key: 'nominal_diameter', label: '公称直径' },
    { key: 'pressure', label: '压力' },
    { key: 'min_stock', label: '最小库存' },
    { key: 'notes', label: '备注' }
  ]
};

// 根据mode定义提交API
const MODE_API = {
  inbound: async (data, materials) => {
    // AI返回的是ledger_name，需要先查找对应的ledger_id
    const { materialAPI, inboundAPI } = await import('../../services/api');
    if (data.ledger_name) {
      // 查找匹配的物料
      const materialList = materials || (await materialAPI.getList({ limit: 1000 })).data;
      const matched = materialList.find(m =>
        m.name.includes(data.ledger_name) || data.ledger_name.includes(m.name)
      );
      if (matched) {
        return inboundAPI.create({ ...data, ledger_id: matched.id });
      } else {
        throw new Error(`未找到物料: ${data.ledger_name}，请先在物料管理中添加`);
      }
    }
    throw new Error('缺少物料名称');
  },
  outbound: async (data, materials) => {
    // AI返回的是ledger_name，需要先查找对应的ledger_id
    const { materialAPI, outboundAPI } = await import('../../services/api');
    if (data.ledger_name) {
      // 查找匹配的物料
      const materialList = materials || (await materialAPI.getList({ limit: 1000 })).data;
      const matched = materialList.find(m =>
        m.name.includes(data.ledger_name) || data.ledger_name.includes(m.name)
      );
      if (matched) {
        return outboundAPI.create({ ...data, ledger_id: matched.id });
      } else {
        throw new Error(`未找到物料: ${data.ledger_name}，请先在物料管理中添加`);
      }
    }
    throw new Error('缺少物料名称');
  },
  material: (data) => import('../../services/api').then(m => m.materialAPI.create(data))
};

const AIPanel = ({ mode = 'material', onSuccess, fillOnly = false, onFill }) => {
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [editableResult, setEditableResult] = useState({});
  const [submitting, setSubmitting] = useState(false);

  const fields = MODE_FIELDS[mode];

  // 处理识别
  const handleRecognize = async () => {
    if (!text.trim()) {
      message.warning('请输入文本或上传文件');
      return;
    }

    setLoading(true);
    try {
      const res = await aiAPI.recognize(mode, { text });
      const data = res.data.data || {};
      setResult(data);
      setEditableResult(data);

      if (fillOnly && onFill) {
        onFill(data);
        message.success('已识别并填充表单');
        setResult(null);
        setEditableResult({});
        setText('');
      } else {
        message.success('识别完成，请确认信息');
      }
    } catch (error) {
      message.error('识别失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  // 处理文件上传
  const handleFileUpload = async (file) => {
    setLoading(true);
    try {
      const res = await aiAPI.recognize(mode, { file });
      const data = res.data.data || {};
      setResult(data);
      setEditableResult(data);

      if (fillOnly && onFill) {
        onFill(data);
        message.success('文件识别并填充表单');
        setResult(null);
        setEditableResult({});
      } else {
        message.success('文件识别完成，请确认信息');
      }
    } catch (error) {
      message.error('文件识别失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
    return false; // 阻止默认上传
  };

  // 编辑结果字段
  const handleFieldChange = (key, value) => {
    setEditableResult(prev => ({ ...prev, [key]: value }));
  };

  // 提交
  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      const apiFn = await MODE_API[mode];
      // inbound和outbound需要先获取物料列表来匹配名称
      let materials = null;
      if (mode === 'inbound' || mode === 'outbound') {
        const { materialAPI } = await import('../../services/api');
        const res = await materialAPI.getList({ limit: 1000 });
        materials = res.data;
      }
      await apiFn(editableResult, materials);
      message.success('提交成功');
      setResult(null);
      setEditableResult({});
      setText('');
      onSuccess?.();
    } catch (error) {
      message.error('提交失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setSubmitting(false);
    }
  };

  // 清空
  const handleClear = () => {
    setResult(null);
    setEditableResult({});
    setText('');
  };

  return (
    <Card className="ai-panel" size="small">
      <div className="ai-panel-header">
        <RobotOutlined /> AI智能识别录入
        <span className="ai-panel-mode">
          {mode === 'inbound' ? '入库' : mode === 'outbound' ? '出库' : '物料'}
        </span>
      </div>

      <Space direction="vertical" style={{ width: '100%' }} size="middle">
        {/* 输入区域 */}
        <div className="ai-panel-input">
          <TextArea
            rows={3}
            placeholder="输入物料描述文本，或上传图片/文件..."
            value={text}
            onChange={e => setText(e.target.value)}
          />
          <div className="ai-panel-actions">
            <Button
              type="primary"
              icon={<RobotOutlined />}
              onClick={handleRecognize}
              loading={loading}
            >
              智能识别
            </Button>
            <Upload
              beforeUpload={handleFileUpload}
              showUploadList={false}
              accept=".jpg,.jpeg,.png,.webp,.docx,.xlsx,.xls,.pdf"
            >
              <Button icon={<UploadOutlined />} loading={loading}>
                上传文件
              </Button>
            </Upload>
          </div>
        </div>

        {/* 支持格式提示 */}
        <div className="ai-panel-hint">
          支持: 文本 · 图片(jpg/png) · Word(docx) · Excel(xlsx) · PDF
        </div>

        {/* 识别结果 */}
        {loading && (
          <div className="ai-panel-loading">
            <Spin tip="AI识别中..." />
          </div>
        )}

        {result && !loading && (
          <div className="ai-panel-result">
            <Alert
              message={fillOnly ? "识别结果已填充到左侧表单" : "识别结果 - 请确认以下信息"}
              type="info"
              showIcon
              closable={!fillOnly}
              onClose={handleClear}
            />
            {!fillOnly && (
              <>
                <div className="ai-panel-fields">
                  {fields.map(field => (
                    <div key={field.key} className="ai-panel-field">
                      <label>
                        {field.label}
                        {field.required && <span className="required">*</span>}
                      </label>
                      <Input
                        value={editableResult[field.key] || ''}
                        onChange={e => handleFieldChange(field.key, e.target.value)}
                        placeholder={`请输入${field.label}`}
                      />
                    </div>
                  ))}
                </div>
                <div className="ai-panel-submit">
                  <Button
                    type="primary"
                    onClick={handleSubmit}
                    loading={submitting}
                  >
                    确认提交
                  </Button>
                  <Button onClick={handleClear}>
                    清空
                  </Button>
                </div>
              </>
            )}
          </div>
        )}
      </Space>
    </Card>
  );
};

export default AIPanel;