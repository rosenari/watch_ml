// ModelTableSection.js

import React, { useState } from 'react';
import { Table, Button } from 'antd';
import { CheckOutlined } from '@ant-design/icons';

function ModelTableSection() {
  const [modelData, setModelData] = useState([]);
  const [selectedModelKeys, setSelectedModelKeys] = useState([]);

  const modelColumns = [
    {
      title: '모델 이름',
      dataIndex: 'modelName',
      key: 'modelName',
      render: (text, record) => (
        <span>
          {record.current ? <CheckOutlined style={{ color: 'green', marginRight: 8 }} /> : null}
          {text}
        </span>
      ),
    },
    { title: '기반 모델', dataIndex: 'baseModel', key: 'baseModel' },
    { title: '정밀도', dataIndex: 'precision', key: 'precision' },
    { title: '재현율', dataIndex: 'recall', key: 'recall' },
    { title: 'mAP@0.5', dataIndex: 'map50', key: 'map50' },
    { title: 'mAP@0.5:0.95', dataIndex: 'map95', key: 'map95' },
    { title: '배포 상태', dataIndex: 'deployStatus', key: 'deployStatus' },
  ];

  const modelRowSelection = {
    selectedRowKeys: selectedModelKeys,
    onChange: (selectedRowKeys) => setSelectedModelKeys(selectedRowKeys),
    getCheckboxProps: (record) => ({ disabled: record.current }),
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        <h3 className="table-title">모델</h3>
        <Button type="default" size="small" className="table-button">배포</Button>
      </div>
      <Table
        className="custom-table"
        rowSelection={modelRowSelection}
        columns={modelColumns}
        dataSource={modelData}
        locale={{ emptyText: '목록 없음' }}
        pagination={false}
      />
    </div>
  );
}

export default ModelTableSection;
