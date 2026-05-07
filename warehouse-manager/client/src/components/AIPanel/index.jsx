import { useState } from 'react';
import { Card, Input, Button, Space, message, Spin, Alert, Table, Checkbox } from 'antd';
import { RobotOutlined, UploadOutlined } from '@ant-design/icons';
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
  const [results, setResults] = useState([]);  // 支持多条记录
  const [selectedKeys, setSelectedKeys] = useState([]);
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
      const data = res.data.data || [];
      const records = Array.isArray(data) ? data : [data];

      if (records.length === 0) {
        message.warning('未识别到任何记录');
        return;
      }

      setResults(records);
      setSelectedKeys(records.map((_, idx) => idx));

      if (fillOnly && onFill && records.length === 1) {
        onFill(records[0]);
        message.success('已识别并填充表单');
        setResults([]);
        setSelectedKeys([]);
        setText('');
      } else if (fillOnly && onFill && records.length > 1) {
        message.success(`识别到${records.length}条记录，请选择要填充的数据`);
      } else {
        message.success(`识别完成，找到${records.length}条记录，请确认`);
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
      const data = res.data.data || [];
      const records = Array.isArray(data) ? data : [data];

      if (records.length === 0) {
        message.warning('未识别到任何记录');
        return;
      }

      setResults(records);
      setSelectedKeys(records.map((_, idx) => idx));

      if (fillOnly && onFill && records.length === 1) {
        onFill(records[0]);
        message.success('文件识别并填充表单');
        setResults([]);
        setSelectedKeys([]);
      } else if (fillOnly && onFill && records.length > 1) {
        message.success(`识别到${records.length}条记录，请选择要填充的数据`);
      } else {
        message.success(`文件识别完成，找到${records.length}条记录，请确认`);
      }
    } catch (error) {
      message.error('文件识别失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
    return false; // 阻止默认上传
  };

  // 编辑结果字段
  const handleFieldChange = (idx, key, value) => {
    setResults(prev => prev.map((r, i) => i === idx ? { ...r, [key]: value } : r));
  };

  // 全选/取消全选
  const handleSelectAll = (checked) => {
    if (checked) {
      setSelectedKeys(results.map((_, idx) => idx));
    } else {
      setSelectedKeys([]);
    }
  };

  // 提交
  const handleSubmit = async () => {
    if (selectedKeys.length === 0) {
      message.warning('请选择要提交的记录');
      return;
    }

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

      const selectedRecords = selectedKeys.map(k => results[k]);
      let successCount = 0;
      for (const record of selectedRecords) {
        try {
          await apiFn(record, materials);
          successCount++;
        } catch (err) {
          console.error('单条提交失败:', err);
        }
      }

      message.success(`成功提交${successCount}/${selectedRecords.length}条记录`);
      setResults([]);
      setSelectedKeys([]);
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
    setResults([]);
    setSelectedKeys([]);
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
            <Button
              icon={<UploadOutlined />}
              loading={loading}
              onClick={() => document.getElementById('ai-file-input').click()}
            >
              上传文件
            </Button>
            <input
              id="ai-file-input"
              type="file"
              accept=".jpg,.jpeg,.png,.webp,.docx,.xlsx,.xls,.pdf"
              style={{ display: 'none' }}
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) {
                  handleFileUpload(file);
                  e.target.value = '';
                }
              }}
            />
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

        {results.length > 0 && !loading && (
          <div className="ai-panel-result">
            <Alert
              message={`识别到${results.length}条记录，请确认后提交`}
              type="info"
              showIcon
              closable
              onClose={handleClear}
            />
            {!fillOnly && (
              <>
                <div style={{ marginTop: 12, marginBottom: 8 }}>
                  <Checkbox
                    checked={selectedKeys.length === results.length}
                    indeterminate={selectedKeys.length > 0 && selectedKeys.length < results.length}
                    onChange={e => handleSelectAll(e.target.checked)}
                  >
                    全选
                  </Checkbox>
                  <span style={{ marginLeft: 8, color: '#888' }}>
                    已选{selectedKeys.length}条
                  </span>
                </div>
                <div className="ai-panel-table-wrapper">
                  <table className="ai-panel-table">
                    <thead>
                      <tr>
                        <th style={{ width: 40 }}></th>
                        {fields.map(f => (
                          <th key={f.key}>{f.label}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {results.map((record, idx) => (
                        <tr key={idx} style={{ background: selectedKeys.includes(idx) ? '#f6ffed' : '#fff' }}>
                          <td>
                            <Checkbox
                              checked={selectedKeys.includes(idx)}
                              onChange={e => {
                                if (e.target.checked) {
                                  setSelectedKeys([...selectedKeys, idx]);
                                } else {
                                  setSelectedKeys(selectedKeys.filter(k => k !== idx));
                                }
                              }}
                            />
                          </td>
                          {fields.map(f => (
                            <td key={f.key}>
                              <Input
                                size="small"
                                value={record[f.key] || ''}
                                onChange={e => handleFieldChange(idx, f.key, e.target.value)}
                                placeholder={f.label}
                              />
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="ai-panel-submit">
                  <Button
                    type="primary"
                    onClick={handleSubmit}
                    loading={submitting}
                  >
                    提交({selectedKeys.length})
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