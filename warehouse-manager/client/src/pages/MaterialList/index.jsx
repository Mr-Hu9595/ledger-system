// warehouse-manager/client/src/pages/MaterialList/index.jsx
import { useState, useEffect } from 'react';
import { Table, Input, Select, Button, Space, Modal, Descriptions, Tag, Form, message } from 'antd';
import { SearchOutlined, PlusOutlined, EyeOutlined, UploadOutlined } from '@ant-design/icons';
import { materialAPI, inboundAPI } from '../../services/api';
import { useNavigate } from 'react-router-dom';

const { Search } = Input;

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
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [isEditing, setIsEditing] = useState(false);
  const [editingForm] = Form.useForm();
  const [categoryOptions, setCategoryOptions] = useState([
    { value: 'equipment', label: '设备' },
    { value: 'material', label: '材料' },
    { value: '监测仪表', label: '监测仪表' },
    { value: '视频监控', label: '视频监控' },
    { value: '雾炮设备', label: '雾炮设备' },
    { value: '洗车机设备', label: '洗车机设备' }
  ]);
  const [unitOptions, setUnitOptions] = useState([
    { value: '个', label: '个' },
    { value: '套', label: '套' },
    { value: '米', label: '米' },
    { value: '吨', label: '吨' },
    { value: '项', label: '项' },
    { value: '批', label: '批' }
  ]);
  const [specificationOptions, setSpecificationOptions] = useState([]);
  const [brandOptions, setBrandOptions] = useState([]);
  const [materialTypeOptions, setMaterialTypeOptions] = useState([]);
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

      // 提取规格、品牌、材质的备选值
      const specs = [...new Set(res.data.map(m => m.specification).filter(Boolean))];
      const brands = [...new Set(res.data.map(m => m.properties?.find(p => p.key === 'brand')?.value).filter(Boolean))];
      const materialTypes = [...new Set(res.data.map(m => m.properties?.find(p => p.key === 'material_type')?.value).filter(Boolean))];

      setSpecificationOptions(specs.map(s => ({ value: s, label: s })));
      setBrandOptions(brands.map(b => ({ value: b, label: b })));
      setMaterialTypeOptions(materialTypes.map(m => ({ value: m, label: m })));
    } catch (error) {
      console.error('获取物料失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = () => {
    editingForm.setFieldsValue({
      name: selectedMaterial.name,
      specification: selectedMaterial.specification,
      category: selectedMaterial.category,
      unit: selectedMaterial.unit,
      brand: selectedMaterial.properties?.find(p => p.key === 'brand')?.value || '',
      material_type: selectedMaterial.properties?.find(p => p.key === 'material_type')?.value || '',
      technical_params: selectedMaterial.properties?.find(p => p.key === 'technical_params')?.value || '',
    });
    setIsEditing(true);
  };

  const handleSave = async () => {
    try {
      const values = await editingForm.validateFields();
      const properties = [];
      if (values.brand) properties.push({ key: 'brand', value: values.brand });
      if (values.material_type) properties.push({ key: 'material_type', value: values.material_type });
      if (values.technical_params) properties.push({ key: 'technical_params', value: values.technical_params });

      await materialAPI.update(selectedMaterial.id, {
        name: values.name,
        specification: values.specification,
        category: values.category,
        unit: values.unit,
        properties: properties,
      });
      message.success('更新成功');
      setIsEditing(false);
      fetchMaterials();
      setDetailModalVisible(false);
    } catch (error) {
      message.error('更新失败');
    }
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
  };

  const handleCloseModal = () => {
    setIsEditing(false);
    setDetailModalVisible(false);
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
        pagination={{
          current: currentPage,
          pageSize: pageSize,
          total: materials.length,
          pageSizeOptions: ['10', '20', '50', '100'],
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条`,
          onChange: (page, size) => {
            setCurrentPage(page);
            setPageSize(size);
          }
        }}
      />

      {/* 详情弹窗 */}
      <Modal
        title="物料详情"
        open={detailModalVisible}
        onCancel={handleCloseModal}
        footer={[
          isEditing ? (
            <Space key="edit-actions">
              <Button onClick={handleCancelEdit}>取消编辑</Button>
              <Button type="primary" onClick={handleSave}>保存</Button>
            </Space>
          ) : (
            <Space key="view-actions">
              <Button onClick={handleCloseModal}>关闭</Button>
              <Button type="primary" onClick={handleEdit}>编辑</Button>
            </Space>
          )
        ]}
      >
        {selectedMaterial && (
          <Form form={editingForm} layout="vertical">
            <Form.Item label="名称" name="name">
              {isEditing ? <Input /> : <span>{selectedMaterial.name}</span>}
            </Form.Item>
            <Form.Item label="规格" name="specification">
              {isEditing ? (
                <Select
                  showSearch
                  allowClear
                  placeholder="选择或输入规格"
                  options={specificationOptions}
                  onSearch={(value) => {
                    if (value && !specificationOptions.some(o => o.value === value)) {
                      setSpecificationOptions([...specificationOptions, { value, label: value }]);
                    }
                  }}
                  filterOption={(input, option) =>
                    option.label.toLowerCase().includes(input.toLowerCase())
                  }
                />
              ) : (
                <span>{selectedMaterial.specification}</span>
              )}
            </Form.Item>
            <Form.Item label="类别" name="category">
              {isEditing ? (
                <Select
                  showSearch
                  allowClear
                  placeholder="选择或输入类别"
                  options={categoryOptions}
                  onSearch={(value) => {
                    if (value && !categoryOptions.some(o => o.value === value)) {
                      setCategoryOptions([...categoryOptions, { value, label: value }]);
                    }
                  }}
                  filterOption={(input, option) =>
                    option.label.toLowerCase().includes(input.toLowerCase())
                  }
                />
              ) : (
                <span>{selectedMaterial.category}</span>
              )}
            </Form.Item>
            <Form.Item label="单位" name="unit">
              {isEditing ? (
                <Select
                  showSearch
                  allowClear
                  placeholder="选择或输入单位"
                  options={unitOptions}
                  onSearch={(value) => {
                    if (value && !unitOptions.some(o => o.value === value)) {
                      setUnitOptions([...unitOptions, { value, label: value }]);
                    }
                  }}
                  filterOption={(input, option) =>
                    option.label.toLowerCase().includes(input.toLowerCase())
                  }
                />
              ) : (
                <span>{selectedMaterial.unit}</span>
              )}
            </Form.Item>
            <Form.Item label="品牌" name="brand">
              {isEditing ? (
                <Select
                  showSearch
                  allowClear
                  placeholder="选择或输入品牌"
                  options={brandOptions}
                  onSearch={(value) => {
                    if (value && !brandOptions.some(o => o.value === value)) {
                      setBrandOptions([...brandOptions, { value, label: value }]);
                    }
                  }}
                  filterOption={(input, option) =>
                    option.label.toLowerCase().includes(input.toLowerCase())
                  }
                />
              ) : (
                <span>{selectedMaterial.properties?.find(p => p.key === 'brand')?.value || '-'}</span>
              )}
            </Form.Item>
            <Form.Item label="材质" name="material_type">
              {isEditing ? (
                <Select
                  showSearch
                  allowClear
                  placeholder="选择或输入材质"
                  options={materialTypeOptions}
                  onSearch={(value) => {
                    if (value && !materialTypeOptions.some(o => o.value === value)) {
                      setMaterialTypeOptions([...materialTypeOptions, { value, label: value }]);
                    }
                  }}
                  filterOption={(input, option) =>
                    option.label.toLowerCase().includes(input.toLowerCase())
                  }
                />
              ) : (
                <span>{selectedMaterial.properties?.find(p => p.key === 'material_type')?.value || '-'}</span>
              )}
            </Form.Item>
            <Form.Item label="技术参数" name="technical_params">
              {isEditing ? <Input.TextArea /> : <span>{selectedMaterial.properties?.find(p => p.key === 'technical_params')?.value || '-'}</span>}
            </Form.Item>
            {!isEditing && (
              <>
                <Descriptions bordered column={2}>
                  <Descriptions.Item label="当前库存">{selectedMaterial.current_stock}</Descriptions.Item>
                  <Descriptions.Item label="最小库存">{selectedMaterial.min_stock}</Descriptions.Item>
                  <Descriptions.Item label="物料编码">{selectedMaterial.material_code}</Descriptions.Item>
                  <Descriptions.Item label="入库状态">{selectedMaterial.inbound_status}</Descriptions.Item>
                </Descriptions>
              </>
            )}
          </Form>
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