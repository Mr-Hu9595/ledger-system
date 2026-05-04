// warehouse-manager/client/src/pages/MaterialList/index.jsx
import { useState, useEffect } from 'react';
import { Table, Input, Select, Button, Space, Modal, Descriptions, Tag } from 'antd';
import { SearchOutlined, PlusOutlined, EyeOutlined, UploadOutlined } from '@ant-design/icons';
import { materialAPI, inboundAPI } from '../../services/api';
import { useNavigate } from 'react-router-dom';

const { Search } = Input;
const { Option } = Select;

const MaterialList = () => {
  const [materials, setMaterials] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [categoryFilter, setCategoryFilter] = useState(null);
  const [statusFilter, setStatusFilter] = useState(null);
  const [selectedMaterial, setSelectedMaterial] = useState(null);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [inboundModalVisible, setInboundModalVisible] = useState(false);
  const [inboundQuantity, setInboundQuantity] = useState(0);
  const navigate = useNavigate();

  useEffect(() => {
    fetchMaterials();
  }, [searchText, categoryFilter, statusFilter]);

  const fetchMaterials = async () => {
    setLoading(true);
    try {
      const params = { limit: 500 };
      if (searchText) params.search = searchText;
      if (categoryFilter) params.category = categoryFilter;
      if (statusFilter) params.inbound_status = statusFilter;

      const res = await materialAPI.getList(params);
      setMaterials(res.data);
    } catch (error) {
      console.error('获取物料失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (value) => {
    setSearchText(value);
  };

  const handleCategoryChange = (value) => {
    setCategoryFilter(value);
  };

  const handleStatusChange = (value) => {
    setStatusFilter(value);
  };

  const showDetail = (record) => {
    setSelectedMaterial(record);
    setDetailModalVisible(true);
  };

  const handleInbound = async () => {
    if (!selectedMaterial || inboundQuantity <= 0) return;

    try {
      await inboundAPI.create({
        ledger_id: selectedMaterial.id,
        inbound_date: new Date().toISOString().split('T')[0],
        quantity: inboundQuantity,
        inbound_operator: '系统管理员'
      });
      setInboundModalVisible(false);
      setInboundQuantity(0);
      fetchMaterials();
    } catch (error) {
      console.error('入库失败:', error);
    }
  };

  const columns = [
    { title: '名称', dataIndex: 'name', key: 'name', fixed: 'left', width: 150 },
    { title: '规格', dataIndex: 'specification', key: 'specification', width: 150 },
    { title: '类别', dataIndex: 'category', key: 'category', width: 100 },
    { title: '单位', dataIndex: 'unit', key: 'unit', width: 80 },
    { title: '当前库存', dataIndex: 'current_stock', key: 'current_stock', width: 100 },
    {
      title: '入库状态',
      dataIndex: 'inbound_status',
      key: 'inbound_status',
      width: 100,
      render: (status) => (
        <Tag color={status === '已入库' ? 'green' : 'orange'}>{status}</Tag>
      )
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right',
      render: (_, record) => (
        <Space>
          <Button size="small" icon={<EyeOutlined />} onClick={() => showDetail(record)}>详情</Button>
          <Button size="small" type="primary" icon={<UploadOutlined />} onClick={() => { setSelectedMaterial(record); setInboundModalVisible(true); }}>入库</Button>
        </Space>
      )
    }
  ];

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Search placeholder="搜索物料名称/规格/编码" onSearch={handleSearch} style={{ width: 300 }} allowClear />
        <Select placeholder="选择类别" onChange={handleCategoryChange} allowClear style={{ width: 150 }}>
          <Option value="equipment">设备</Option>
          <Option value="material">材料</Option>
          <Option value="监测仪表">监测仪表</Option>
        </Select>
        <Select placeholder="入库状态" onChange={handleStatusChange} allowClear style={{ width: 120 }}>
          <Option value="待入库">待入库</Option>
          <Option value="已入库">已入库</Option>
        </Select>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/materials/create')}>手动录入</Button>
      </Space>

      <Table
        columns={columns}
        dataSource={materials}
        rowKey="id"
        loading={loading}
        scroll={{ x: 1200 }}
        pagination={{ pageSize: 10, showSizeChanger: true, showTotal: (total) => `共 ${total} 条` }}
      />

      {/* 详情弹窗 */}
      <Modal
        title="物料详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>关闭</Button>,
          <Button key="inbound" type="primary" onClick={() => { setDetailModalVisible(false); setInboundModalVisible(true); }}>入库</Button>
        ]}
      >
        {selectedMaterial && (
          <Descriptions bordered column={2}>
            <Descriptions.Item label="名称">{selectedMaterial.name}</Descriptions.Item>
            <Descriptions.Item label="规格">{selectedMaterial.specification}</Descriptions.Item>
            <Descriptions.Item label="类别">{selectedMaterial.category}</Descriptions.Item>
            <Descriptions.Item label="单位">{selectedMaterial.unit}</Descriptions.Item>
            <Descriptions.Item label="当前库存">{selectedMaterial.current_stock}</Descriptions.Item>
            <Descriptions.Item label="最小库存">{selectedMaterial.min_stock}</Descriptions.Item>
            <Descriptions.Item label="物料编码">{selectedMaterial.material_code}</Descriptions.Item>
            <Descriptions.Item label="入库状态">{selectedMaterial.inbound_status}</Descriptions.Item>
            <Descriptions.Item label="品牌" span={2}>{selectedMaterial.properties?.find(p => p[0] === 'brand')?.[1] || '-'}</Descriptions.Item>
            <Descriptions.Item label="材质" span={2}>{selectedMaterial.properties?.find(p => p[0] === 'material_type')?.[1] || '-'}</Descriptions.Item>
            <Descriptions.Item label="技术参数" span={2}>{selectedMaterial.properties?.find(p => p[0] === 'technical_params')?.[1] || '-'}</Descriptions.Item>
          </Descriptions>
        )}
      </Modal>

      {/* 入库弹窗 */}
      <Modal
        title="入库"
        open={inboundModalVisible}
        onCancel={() => setInboundModalVisible(false)}
        onOk={handleInbound}
      >
        <p>物料: {selectedMaterial?.name}</p>
        <p>当前库存: {selectedMaterial?.current_stock}</p>
        <p>
          入库数量:
          <input
            type="number"
            value={inboundQuantity}
            onChange={(e) => setInboundQuantity(parseFloat(e.target.value) || 0)}
            style={{ marginLeft: 8, width: 100 }}
          />
        </p>
      </Modal>
    </div>
  );
};

export default MaterialList;