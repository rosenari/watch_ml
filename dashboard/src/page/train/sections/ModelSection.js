// ModelTableSection.js

import React, { useState, useEffect } from 'react';
import { Table, Button, Tag, Spin, Progress, message  } from 'antd';
import { blue } from '@ant-design/colors';
import { useModel } from 'hooks';
import { CheckOutlined, LoadingOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import { deployModel, undeployModel } from 'api/ml';

function ModelTableSection({ reloadModelList }) {
  const { modelData } = useModel();
  const [selectedModelKeys, setSelectedModelKeys] = useState([]);

  const modelColumns = [
    {
      title: '모델 이름',
      dataIndex: 'modelName',
      key: 'modelName',
      render: (text, record) => (
        <span>
          {text}
          {record.version && (
            <Tag color="blue" style={{ marginLeft: 8, fontSize: '10px', padding: '3px', lineHeight: '8px', borderRadius: '2px' }}>
              {`v${record.version}`}
            </Tag>
          )}
          {/^\d+$/.test(record.status) ? (
            <>
              <LoadingOutlined spin style={{ marginRight: '5px' }} />
              <Progress
                percent={record.status}
                size="small"
                steps={10}
                strokeColor={blue[6]}
                style={{ width: 0, marginLeft: 3, fontSize: '10px' }}
              />
            </>
          ) : (
            <>
              {record.status === 'complete' && <CheckOutlined style={{ color: 'green', marginRight: 8 }} />}
              {record.status === 'failed' && <ExclamationCircleOutlined style={{ color: 'red', marginRight: 8 }} />}
              {(record.status === 'running' || record.status === 'pending') && <Spin indicator={<LoadingOutlined spin />} size="small" />}
            </>
          )}
        </span>
      ),
    },
    { title: '기반 모델', dataIndex: 'baseModelName', key: 'baseModelName' },
    { title: '정밀도', dataIndex: 'precision', key: 'precision' },
    { title: '재현율', dataIndex: 'recall', key: 'recall' },
    { title: 'mAP@0.5', dataIndex: 'map50', key: 'map50' },
    { title: 'mAP@0.5:0.95', dataIndex: 'map50_95', key: 'map50_95' },
    { title: '배포 상태', dataIndex: 'isDeploy', key: 'isDeploy' },
  ];

  const modelRowSelection = {
    selectedRowKeys: selectedModelKeys,
    onChange: (selectedRowKeys) => {
      setSelectedModelKeys(selectedRowKeys.slice(-1));
    },
    getCheckboxProps: (record) => ({ disabled: record.current }),
  };
  useEffect(() =>{
    reloadModelList();
  }, [reloadModelList]);

  const handleDeploy = async () => {
    if (selectedModelKeys.length === 0) {
      message.warning('배포할 모델을 선택해주세요.');
    }

    await deployModel({ modelName: selectedModelKeys[0] });
    setSelectedModelKeys([]);

    reloadModelList();
  }

  const handleUnDeploy = async () => {
    if (selectedModelKeys.length === 0) {
      message.warning('배포 해제할 모델을 선택해주세요.');
    }

    await undeployModel({ modelName: selectedModelKeys[0] });
    setSelectedModelKeys([]);

    reloadModelList();
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 className="table-title">모델</h3>
        <div>
          <Button type="default" size="small" className="table-button" style={{ marginRight: '5px' }} onClick={handleDeploy}>배포</Button>
          <Button type="default" size="small" className="table-button" onClick={handleUnDeploy}>배포 해제</Button>
        </div>
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
