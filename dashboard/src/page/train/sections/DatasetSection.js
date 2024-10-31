// FileUploadSection.js

import React, { useState, useEffect, useCallback } from 'react';
import { Upload, Table, Button, message, Spin } from 'antd';
import { InboxOutlined, CheckOutlined, LoadingOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import { datasetUpload, getDatasetList, deleteDataset, validDataset, getDatasetStatus } from 'api/dataset';
import { useExecuteRepeat, useModel, useDataset } from 'hooks';
import ModelCreateModal from './components/ModelCreateModal';
import "./DatasetSection.css";

const { Dragger } = Upload;

function DatasetSection() {
  const { modelData, setModelData, state } = useModel();
  const { datasetData, setDatasetData } = useDataset();
  const [selectedDatasetKeys, setSelectedDatasetKeys] = useState([]);
  const [fileList, setFileList] = useState([]);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const { executeRepeat, stopExecution } = useExecuteRepeat();

  const logicToPolling = useCallback(async () => {
    const validFiles = await getDatasetStatus();
    const modifiedDataset = state.dataset.map((dataset) => {
      const updatedFile = validFiles.find((file) => file.file_name === dataset.fileName);
      return {
        ...dataset,
        status: updatedFile ? updatedFile.status : dataset.status,
      };
    });
    setDatasetData(modifiedDataset);

    const runningCount = modifiedDataset.filter(
      (dataset) => dataset.status === 'running' || dataset.status === 'pending'
    ).length;
  
    if (runningCount === 0) {
      stopExecution();
    }
  }, [state, setDatasetData, stopExecution]);
  
  const startValidFilesPolling = useCallback(() => {
    executeRepeat(logicToPolling, 500);
  }, [executeRepeat, logicToPolling]);

  const reloadFileList = useCallback(async () => {
    try {
      const datasetList = await getDatasetList();
      const formatted_list = datasetList.map((dataset) => ({
        key: dataset.file_name,
        fileName: dataset.file_name,
        uploadDate: dataset.file_meta.creation_time,
        fileSize: dataset.file_meta.filesize,
        status: dataset.status
      }));

      setDatasetData([...formatted_list]);

      const runningCount = datasetList.filter((dataset) => dataset.status === 'running' || dataset.status === 'pending').length
      if (runningCount > 0) {
        startValidFilesPolling();
      }
    } catch (e) {
      console.error(`파일 목록 불러오기 실패: ${e}`);
      stopExecution();
    }
  }, [setDatasetData, stopExecution, startValidFilesPolling]);

  useEffect(() => {
    reloadFileList();
  }, [reloadFileList]);

  const handleUpload = async () => {
    if (fileList.length === 0) {
      message.warning('업로드할 파일이 없습니다.');
      return;
    }

    for (const file of fileList) {
      try {
        const data = await datasetUpload(file);
        if (data.file_name !== file.name) {
          throw new Error('정상적으로 업로드 되지 않음.');
        }
        message.success(`${file.name} 업로드 성공`);
        reloadFileList();
      } catch (error) {
        console.error(error);
        message.error(`${file.name} 업로드 실패`);
      }
    }
    setFileList([]);
  };

  const handleReset = () => {
    setFileList([]); 
    message.success('파일 목록이 초기화되었습니다.');
  };

  const handleDelete = async () => {
    if (selectedDatasetKeys.length === 0) {
      message.warning('삭제할 파일을 지정하지 않았습니다.');
    }

    for (const fileName of selectedDatasetKeys) {
      try {
        const result = await deleteDataset(fileName);
        result ? message.success(`${fileName} 삭제 성공`) : message.error(`${fileName} 삭제 실패`);
      } catch (error) {
        message.error(`${fileName} 삭제 실패`);
      }
    }

    reloadFileList();
  };

  const handleValid = async () => {
    if (selectedDatasetKeys.length === 0) {
      message.warning('검사할 파일을 지정하지 않았습니다.');
    }

    await validDataset(selectedDatasetKeys);
    setSelectedDatasetKeys([]);

    reloadFileList();
  };

  const handleModelCreate = async () => {
    if (selectedDatasetKeys.length === 0) {
      message.warning('모델 생성을 위한 파일을 지정하지 않았습니다.');
      return;
    }

    const hasIncompleteFiles = datasetData
    .filter((dataset) => dataset.status !== 'complete')
    .some((dataset) => selectedDatasetKeys.includes(dataset.fileName));

    if (hasIncompleteFiles) {
      message.warning('선택한 파일 중 검사되지 않은 파일이 있습니다.');
      return;
    }

    setIsModalVisible(true);

  }

  const uploadProps = {
    multiple: true,
    beforeUpload: (file) => {
      setFileList((prevList) => [...prevList, file]);
      return false; 
    },
    fileList,
    onRemove: (file) => setFileList((prevList) => prevList.filter((item) => item.uid !== file.uid)),
  };

  const datasetColumns = [
    {
      title: '파일 이름',
      dataIndex: 'fileName',
      key: 'fileName',
      render: (text, record) => (
        <div>
          <span style={{ marginRight: '8px' }}>{text}</span>
          {record.status === 'complete' && <CheckOutlined style={{ color: 'green', marginRight: 8 }} />}
          {record.status === 'failed' && <ExclamationCircleOutlined style={{ color: 'red', marginRight: 8 }} />}
          {(record.status === 'running' || record.status === 'pending') && <Spin indicator={<LoadingOutlined spin />} size="small" />}
        </div>
      ),
    },
    {
      title: '파일 크기',
      dataIndex: 'fileSize',
      key: 'fileSize',
      width: 200,
    },
    {
      title: '업로드 날짜',
      dataIndex: 'uploadDate',
      key: 'uploadDate',
      width: 200,
    },
  ];

  const datasetRowSelection = {
    selectedRowKeys: selectedDatasetKeys,
    onChange: (selectedRowKeys) => setSelectedDatasetKeys(selectedRowKeys),
  };

  return (
    <div>
      <Dragger {...uploadProps} style={{ marginBottom: '20px' }}>
        <p className="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p className="ant-upload-text">데이터셋 아카이브를 업로드하세요 (zip)</p>
      </Dragger>

      <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '20px' }}>
        <Button className="upload-button" size="small" type="default" onClick={handleUpload} style={{ marginRight: '5px' }}>업로드</Button>
        <Button className="reset-button" size="small" type="default" onClick={handleReset}>초기화</Button>
      </div>

      <ModelCreateModal 
        modelData={modelData}
        isModalVisible={isModalVisible} 
        setIsModalVisible={setIsModalVisible} 
        selectedDatasetKeys={selectedDatasetKeys} 
        setSelectedDatasetKeys={setSelectedDatasetKeys} />

      <div style={{ marginBottom: '20px' }}>
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
          <h3 className="table-title">데이터셋</h3>
          <div>
            <Button type="default" size="small" className="table-button" style={{ marginRight: '5px' }} onClick={handleValid}>파일검사</Button>
            <Button type="default" size="small" className="table-button" style={{ marginRight: '5px' }} onClick={handleDelete}>파일삭제</Button>
            <Button type="default" size="small" className="table-button" onClick={handleModelCreate}>모델 생성</Button>
          </div>
        </div>
        <Table
          className="custom-table"
          rowSelection={datasetRowSelection}
          columns={datasetColumns}
          dataSource={datasetData}
          locale={{ emptyText: '목록 없음' }}
          pagination={false}
        />
      </div>
    </div>
  );
}

export default DatasetSection;
