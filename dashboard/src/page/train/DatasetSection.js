// FileUploadSection.js

import React, { useState, useEffect, useCallback } from 'react';
import { Upload, Table, Button, message, Spin } from 'antd';
import { InboxOutlined, CheckOutlined, LoadingOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import { fileUpload, getFileList, deleteFile, validFiles, getValidFiles } from 'api/files';
import { useExecuteRepeat } from 'hooks';

const { Dragger } = Upload;

function DatasetSection() {
  const [datasetData, setDatasetData] = useState([]);
  const [selectedDatasetKeys, setSelectedDatasetKeys] = useState([]);
  const [fileList, setFileList] = useState([]); 
  const [validDatasetData, setValidDatasetData] = useState([]);
  const { executeRepeat, stopExecution } = useExecuteRepeat();

  const reloadFileList = useCallback(async () => {
    try {
      const list = await getFileList();
      const validDatasetDataMap = validDatasetData.reduce((acc, { file_name, status }) => {
        acc[file_name] = status;
        return acc;
      }, {});

      const formatted_list = list.map((file) => ({
        key: file.file_name,
        fileName: file.file_name,
        uploadDate: file.creation_date,
        fileSize: file.file_size,
        valid: (file.file_name in validDatasetDataMap) ? validDatasetDataMap[file.file_name] : ''
      }));
    
      setDatasetData([...formatted_list]);
    } catch (e) {
      console.error(`파일 목록 불러오기 실패: ${e}`);
      stopExecution();
    }
  }, [validDatasetData, stopExecution]);

  const logicToPolling = useCallback(async () => {
    const validFiles = await getValidFiles();
    setValidDatasetData([...validFiles]);
  }, []);

  useEffect(() => {
    reloadFileList();
    const filterData = validDatasetData.filter((data) => (data.status === 'pending' || data.status === 'running'));
    if (filterData.length === 0) {
      stopExecution();
    }
  }, [validDatasetData, reloadFileList, stopExecution]);

  const startValidFilesPolling = useCallback(() => {
    executeRepeat(logicToPolling, 500);
  }, [executeRepeat, logicToPolling]);

  useEffect(() => {
    startValidFilesPolling();
  }, [startValidFilesPolling]);

  const handleUpload = async () => {
    if (fileList.length === 0) {
      message.warning('업로드할 파일이 없습니다.');
      return;
    }

    for (const file of fileList) {
      try {
        const data = await fileUpload(file);
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
        const result = await deleteFile(fileName);
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

    validFiles(selectedDatasetKeys);
    setSelectedDatasetKeys([]);
    startValidFilesPolling();
  };

  const uploadProps = {
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
          {record.valid === 'complete' && <CheckOutlined style={{ color: 'green', marginRight: 8 }} />}
          {record.valid === 'failed' && <ExclamationCircleOutlined style={{ color: 'red', marginRight: 8 }} />}
          {(record.valid === 'running' || record.valid === 'pending') && <Spin indicator={<LoadingOutlined spin />} size="small" />}
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

      <div style={{ marginBottom: '20px' }}>
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
          <h3 className="table-title">데이터셋</h3>
          <div>
            <Button type="default" size="small" className="table-button" style={{ marginRight: '5px' }} onClick={handleValid}>파일검사</Button>
            <Button type="default" size="small" className="table-button" onClick={handleDelete}>파일삭제</Button>
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
