import React, { useState, useEffect } from 'react';
import { Upload, Table, Button, message, Spin } from 'antd';
import { InboxOutlined, CheckOutlined, LoadingOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import { datasetUpload, deleteDataset, validDataset, getDatasetList, getDatasetStatus } from 'api/dataset';
import { useInfiniteQuery, useQuery } from 'react-query';
import { useDataset } from 'hooks';
import { useInView } from 'react-intersection-observer';
import ModelCreateModal from './components/ModelCreateModal';
import { formatDatasetList } from 'formatter';
import "./DatasetSection.css";

const { Dragger } = Upload;

function DatasetSection({ setModelPollEnabled }) {
  const { datasetData, setDatasetData } = useDataset();
  const [selectedDatasetKeys, setSelectedDatasetKeys] = useState([]);
  const [fileList, setFileList] = useState([]);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [pollEnabled, setPollEnabled] = useState(true);
  const [ref, inView] = useInView();

  // 무한 스크롤 로직
  const {
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    refetch
  } = useInfiniteQuery(
    'datasetList',
    ({ pageParam = null }) => getDatasetList(pageParam),
    {
      getNextPageParam: (lastPage) =>{
        return lastPage.length ? lastPage[lastPage.length - 1].id : undefined;
      },
      onSuccess: (data) => {
        setTimeout(() => {
          const formattedData = data.pages.flatMap(formatDatasetList);
          setDatasetData(formattedData);
        });
      },
      cacheTime: 0,
      staleTime: 0,
    }
  );

  useEffect(() => {
    if (inView && hasNextPage) {
      fetchNextPage();
    }
  }, [inView, hasNextPage, fetchNextPage]);

  // 폴링 로직
  useQuery(
    'datasetStatus',
    getDatasetStatus,
    {
      refetchInterval: pollEnabled ? 500 : false,
      onSuccess: async (newStatusData) => {
        const updatedData = datasetData.map((item) => ({
          ...item,
          status: newStatusData.find(status => status.id === item.key)?.status || item.status,
        }));
        setDatasetData(updatedData);

        if (!updatedData.some(item => item.status === 'running' || item.status === 'pending')) {
          setPollEnabled(false);
          await refetch();
        }
      },
      cacheTime: 0,
      staleTime: 0,
    }
  );

  useEffect(() => {
    if (pollEnabled) {
      refetch();
    }
  }, [pollEnabled, refetch]);

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
        await refetch();
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
      return;
    }

    setSelectedDatasetKeys([]);
    for (const datasetId of selectedDatasetKeys) {
      const dataset = datasetData.find(dataset => dataset.key === datasetId);
      const fileName = dataset.fileName;

      try {
        const result = await deleteDataset(datasetId);
        result ? message.success(`${fileName} 삭제 성공`) : message.error(`${fileName} 삭제 실패`);
        await refetch();
      } catch (error) {
        message.error(`${fileName} 삭제 실패`);
      }
    }
  };

  const handleValid = async () => {
    if (selectedDatasetKeys.length === 0) {
      message.warning('검사할 파일을 지정하지 않았습니다.');
      return;
    }
    setSelectedDatasetKeys([]);

    await validDataset(selectedDatasetKeys);
    message.info('파일 검사 요청');
    setPollEnabled(true);  // 검사 후 폴링 활성화
  };

  const handleModelCreate = () => {
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
  };

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
        isModalVisible={isModalVisible} 
        setIsModalVisible={setIsModalVisible} 
        selectedDatasetKeys={selectedDatasetKeys} 
        setSelectedDatasetKeys={setSelectedDatasetKeys}
        setModelPollEnabled={setModelPollEnabled}
      />

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
          scroll={{ y: 200 }}
          onRow={(record, index) => ({
            ref: index === datasetData.length - 1 ? ref : null,
          })}
          footer={() => (
            isFetchingNextPage ? <Spin indicator={<LoadingOutlined spin />} /> : null
          )}
        />
      </div>
    </div>
  );
}

export default DatasetSection;
