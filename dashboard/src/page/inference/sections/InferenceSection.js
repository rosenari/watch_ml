// FileUploadSection.js

import React, { useState, useEffect, useCallback } from 'react';
import { Upload, Table, Button, message, Spin, Select } from 'antd';
import { useInView } from 'react-intersection-observer';
import { FileImageOutlined, LoadingOutlined, ExclamationCircleOutlined, DownloadOutlined  } from '@ant-design/icons';
import { originalFileUpload, generateInferenceFile, deleteOriginalFile, downloadFileLink } from 'api/inference';
import { useInference } from 'hooks';
import { formatInferenceList } from 'reloader';
import { getModelList } from 'api/ml';
import { getInferenceList } from 'api/inference';
import "./InferenceSection.css";

const { Dragger } = Upload;
const { Option } = Select;

function InferenceSection({ reloadInferenceList }) {
  const { inferenceData, setInferenceData } = useInference();
  const [ selectedInferenceKeys, setSelectedInferenceKeys] = useState([]);
  const [ fileList, setFileList] = useState([]);
  const [selectedModel, setSelectedModel] = useState(null);
  const [ modelList, setModelList] = useState([]);
  const [hasMore, setHasMore] = useState(true); 
  const [ref, inView] = useInView();
  
  const loadMoreData = useCallback(async (lastId) => {
    if (!hasMore) return;

    const newData = await getInferenceList(lastId);
    if (newData.length === 0) {
      setHasMore(false); // 빈 배열이면 더 이상 로드하지 않음
      return;
    }

    setInferenceData([
      ...inferenceData,
      ...formatInferenceList(newData),
    ]);

    return newData.length ? newData[newData.length - 1].id : null;
  }, [hasMore, setInferenceData, inferenceData]);

  useEffect(() => {
    if (inView && hasMore) {
      const lastId = inferenceData.length ? inferenceData[inferenceData.length - 1].key : null;
      loadMoreData(lastId);
    }
  }, [inView, hasMore, inferenceData, loadMoreData]);

  useEffect(() => {
    reloadInferenceList();
    reloadModelList();
  }, [reloadInferenceList]);

  const reloadModelList = async () => {
    setModelList(await getModelList());
  }

  const handleUpload = async () => {
    if (fileList.length === 0) {
      message.warning('업로드할 파일이 없습니다.');
      return;
    }

    for (const file of fileList) {
      try {
        const data = await originalFileUpload(file);
        if (data.original_file_name !== file.name) {
          throw new Error('정상적으로 업로드 되지 않음.');
        }
        message.success(`${file.name} 업로드 성공`);
        reloadInferenceList();
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
    if (selectedInferenceKeys.length === 0) {
      message.warning('삭제할 파일을 지정하지 않았습니다.');
    }

    for (const inferenceFileId of selectedInferenceKeys) {
      const result = await deleteOriginalFile(inferenceFileId);
      const inferenceFile = inferenceData.find(inference => inference.key === inferenceFileId);
      const fileName = inferenceFile.fileName;
      try {
        result ? message.success(`${fileName} 삭제 성공`) : message.error(`${fileName} 삭제 실패`);
      } catch (error) {
        message.error(`${fileName} 삭제 실패`);
      }
    }

    setSelectedInferenceKeys([]);
    reloadInferenceList();
  };

  const handleGenerateInferenceFile = async () => {
    if (selectedInferenceKeys.length === 0) {
      message.warning('추론을 위한 파일을 지정하지 않았습니다.');
      return;
    }

    if (selectedModel == null) {
      message.warning('추론 모델을 선택해주세요.');
      return;
    }

    await generateInferenceFile({ inferenceFileId: selectedInferenceKeys[0], modelId: selectedModel });

    reloadInferenceList();
    setSelectedInferenceKeys([]);
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

  const inferenceColumns = [
    {
      title: '원본파일',
      dataIndex: 'originalFileName',
      key: 'originalFileName',
      render: (text, record) => (
        <div>
          <span style={{ marginRight: '8px' }}>{text}</span>
          <a href={downloadFileLink(record.originalFileId)} download>
            <DownloadOutlined style={{ marginRight: 8 }} />
          </a>
          {record.status === 'failed' && <ExclamationCircleOutlined style={{ color: 'red', marginRight: 8 }} />}
          {(record.status === 'running' || record.status === 'pending') && <Spin indicator={<LoadingOutlined spin />} size="small" />}
        </div>
      ),
    },
    {
      title: '원본파일 크기',
      dataIndex: 'originalFileSize',
      key: 'originalFileSize',
    },
    {
      title: '추론파일',
      dataIndex: 'generatedFileName',
      key: 'generatedFileName',
      render: (text, record) => {
        return <div>
          <span style={{ marginRight: '8px' }}>{text}</span>
          {record.generatedFileName !== '-' && (
            <a href={downloadFileLink(record.generatedFileId)} download>
              <DownloadOutlined style={{ marginRight: 8 }} />
            </a>
          )}
        </div>
      },
    },
    {
      title: '추론파일 크기',
      dataIndex: 'generatedFileSize',
      key: 'generatedFileSize',
    },
  ];

  const inferenceRowSelection = {
    selectedRowKeys: selectedInferenceKeys,
    onChange: (selectedRowKeys) => {
      setSelectedInferenceKeys(selectedRowKeys.slice(-1));
    },
    getCheckboxProps: (record) => ({ disabled: record.current })
  };

  return (
    <div>
      <Dragger {...uploadProps} style={{ marginBottom: '20px' }}>
        <p className="ant-upload-drag-icon">
          <FileImageOutlined />
        </p>
        <p className="ant-upload-text">파일을 업로드하세요.</p>
        <p className="ant-upload-text">jpg, jpeg, png, mov, mp4, avi, mkv</p>
      </Dragger>

      <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '20px' }}>
        <Button className="upload-button" size="small" type="default" onClick={handleUpload} style={{ marginRight: '5px' }}>업로드</Button>
        <Button className="reset-button" size="small" type="default" onClick={handleReset}>초기화</Button>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
          <h3 className="table-title">파일</h3>
          <div>
            <Select
              placeholder="추론 모델을 선택하세요"
              style={{ width: 200, marginRight: '5px'}}
              value={selectedModel}
              onChange={(value) => setSelectedModel(value)}
            >
              {modelList.filter((model) => model.status === 'complete' && model.is_deploy === true).map((model) => (
                    <Option key={model.id} value={model.id}>
                        {model.model_name}
                    </Option>
              ))}
            </Select>
            <Button type="default" size="small" className="table-button" style={{ marginRight: '5px' }} onClick={handleGenerateInferenceFile}>추론</Button>
            <Button type="default" size="small" className="table-button" style={{ marginRight: '5px' }} onClick={handleDelete}>파일삭제</Button>
          </div>
        </div>
        <Table
          className="custom-table"
          rowSelection={inferenceRowSelection}
          columns={inferenceColumns}
          dataSource={inferenceData}
          locale={{ emptyText: '목록 없음' }}
          pagination={false}
          scroll={{ y: 200 }}
          onRow={( _, index ) => ({
            ref: index === inferenceData.length - 1 ? ref : null,
          })}
        />
      </div>
    </div>
  );
}

export default InferenceSection;
