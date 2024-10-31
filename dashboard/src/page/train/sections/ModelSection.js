// ModelTableSection.js

import React, { useState, useCallback, useEffect } from 'react';
import { Table, Button, Tag } from 'antd';
import { useModel } from 'hooks';
import { getModelList, getModelStatus, deployModel, undeployModel } from 'api/ml';

function ModelTableSection() {
  const { modelData, setModelData, state } = useModel();
  const [selectedModelKeys, setSelectedModelKeys] = useState([]);

  const modelColumns = [
    {
      title: '모델 이름',
      dataIndex: 'modelName',
      key: 'modelName',
      render: (text, record) => (
        <span>
          {text}
          {record.version && <Tag color="blue" style={{ marginLeft: 8, fontSize: '10px', padding: '3px', lineHeight: '8px', borderRadius: '2px' }}>{`v${record.version}`}</Tag>}
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

  const reloadModelList = useCallback(async () => {
    try {
      const modelList = await getModelList();
      const formatted_list = modelList.map((model) => ({
        key: model.model_name,
        modelName: model.model_name,
        version: model.version,
        map50: model.map50 ?? '-',
        map50_95: model.map50_95 ?? '-',
        precision: model.precision ?? '-',
        recall: model.recall ?? '-',
        classes: model.classes ?? '-',
        status: model.status,
        isDeploy: model.is_deploy ? '🚀' : '-',
        baseModelName: model.base_model ? model.base_model.model_name : '-'
      }));

      setModelData([...formatted_list]);

      const runningCount = modelList.filter((model) => model.status === 'running' || model.status === 'pending').length
      if (runningCount > 0) {
        //startValidFilesPolling();
      }
    } catch (e) {
      console.error(`파일 목록 불러오기 실패: ${e}`);
      //stopExecution();
    }
  }, [setModelData]);

  useEffect(() =>{
    reloadModelList();
  }, [reloadModelList]);

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 className="table-title">모델</h3>
        <div>
          <Button type="default" size="small" className="table-button" style={{ marginRight: '5px' }}>배포</Button>
          <Button type="default" size="small" className="table-button">배포 해제</Button>
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
