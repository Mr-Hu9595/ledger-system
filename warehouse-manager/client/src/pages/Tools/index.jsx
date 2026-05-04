// warehouse-manager/client/src/pages/Tools/index.jsx
import { useState } from 'react';
import { Card, Button, Upload, message, Table, Typography, Space } from 'antd';
import { DownloadOutlined, UploadOutlined, SyncOutlined, FileExcelOutlined } from '@ant-design/icons';
import { toolsAPI } from '../../services/api';

const { Title } = Typography;

const Tools = () => {
  const [loading, setLoading] = useState(false);
  const [syncResult, setSyncResult] = useState(null);

  const handleImport = async (file) => {
    setLoading(true);
    try {
      const res = await toolsAPI.importExcel(file);
      message.success(res.data.message);
    } catch (error) {
      message.error('导入失败');
    } finally {
      setLoading(false);
    }
    return false; // 阻止默认上传
  };

  const handleExportMaterials = async () => {
    setLoading(true);
    try {
      const res = await toolsAPI.exportMaterials();
      const blob = new Blob([res.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `物料清单_${new Date().toISOString().split('T')[0]}.xlsx`;
      a.click();
      window.URL.revokeObjectURL(url);
      message.success('导出成功');
    } catch (error) {
      message.error('导出失败');
    } finally {
      setLoading(false);
    }
  };

  const handleExportInbounds = async () => {
    setLoading(true);
    try {
      const res = await toolsAPI.exportInbounds();
      const blob = new Blob([res.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `入库记录_${new Date().toISOString().split('T')[0]}.xlsx`;
      a.click();
      window.URL.revokeObjectURL(url);
      message.success('导出成功');
    } catch (error) {
      message.error('导出失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async () => {
    setLoading(true);
    try {
      const res = await toolsAPI.syncReport();
      setSyncResult(res.data);
      message.success('同步成功');
    } catch (error) {
      message.error('同步失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <Title level={3}>工具</Title>

      <Space direction="vertical" style={{ width: '100%' }} size="large">
        <Card title="数据导入">
          <Upload beforeUpload={handleImport} showUploadList={false}>
            <Button type="primary" icon={<UploadOutlined />} loading={loading}>
              导入Excel
            </Button>
          </Upload>
        </Card>

        <Card title="数据导出">
          <Space>
            <Button icon={<DownloadOutlined />} onClick={handleExportMaterials} loading={loading}>
              导出物料清单
            </Button>
            <Button icon={<DownloadOutlined />} onClick={handleExportInbounds} loading={loading}>
              导出入库记录
            </Button>
          </Space>
        </Card>

        <Card title="报表同步">
          <Button type="primary" icon={<SyncOutlined />} onClick={handleSync} loading={loading}>
            同步报表
          </Button>
          {syncResult && (
            <div style={{ marginTop: 16 }}>
              <p>物料总数: {syncResult.materials_count}</p>
              <p>入库记录: {syncResult.inbounds_count}</p>
              <p>出库记录: {syncResult.outbounds_count}</p>
              <p>最后同步: {syncResult.last_sync}</p>
            </div>
          )}
        </Card>
      </Space>
    </div>
  );
};

export default Tools;