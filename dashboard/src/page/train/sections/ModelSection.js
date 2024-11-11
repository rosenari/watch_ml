import React, { useState, useEffect } from 'react';
import { Table, Button, Tag, Spin, Progress, message } from 'antd';
import { blue } from '@ant-design/colors';
import { useInfiniteQuery, useQuery } from 'react-query';
import { useModel } from 'hooks';
import { useInView } from 'react-intersection-observer';
import { CheckOutlined, LoadingOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import { deployModel, undeployModel, getModelList, getModelStatus } from 'api/ml';
import { formatModelList } from 'formatter';

function ModelTableSection({ modelPollEnabled, setModelPollEnabled }) {
  const { modelData, setModelData } = useModel();
  const [selectedModelKeys, setSelectedModelKeys] = useState([]);
  const [ref, inView] = useInView();
  const [initialized, setInitialized] = useState(false);

  // 무한 스크롤 로직
  const {
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    refetch,
  } = useInfiniteQuery(
    'modelList',
    ({ pageParam = null }) => getModelList(pageParam),
    {
      getNextPageParam: (lastPage) => {
        return lastPage.length ? lastPage[lastPage.length - 1].id : undefined;
      },
      onSuccess: (data) => {
        setTimeout(() => {
          const formattedData = data.pages.flatMap(formatModelList);
          setModelData(formattedData);
          setInitialized(true);
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
    'modelStatus',
    getModelStatus,
    {
      refetchInterval: modelPollEnabled ? 500 : false,
      onSuccess: async (newStatusData) => {
        if (!initialized) {
          return;
        }

        const updatedData = modelData.map((item) => ({
          ...item,
          status: newStatusData.find(status => status.id === item.key)?.status || item.status,
        }));
        setModelData(updatedData);

        if (!updatedData.some(item => item.status === 'running' || item.status === 'pending' || /^\d+$/.test(item.status))) {
          setModelPollEnabled(false);
          await refetch();
        }
      },
      cacheTime: 0,
      staleTime: 0,
    }
  );

  useEffect(() => {
    if (modelPollEnabled) {
      refetch();
    }
  }, [modelPollEnabled, refetch]);

  const handleDeploy = async () => {
    if (selectedModelKeys.length === 0) {
      message.warning('배포할 모델을 선택해주세요.');
      return;
    }
    setSelectedModelKeys([]);

    await deployModel({ modelId: selectedModelKeys[0] });
    message.info('모델 배포 요청');
    setModelPollEnabled(true);
  };

  const handleUnDeploy = async () => {
    if (selectedModelKeys.length === 0) {
      message.warning('배포 해제할 모델을 선택해주세요.');
      return;
    }
    setSelectedModelKeys([]);

    await undeployModel({ modelId: selectedModelKeys[0] });
    message.info('모델 배포 해제 요청');
    setModelPollEnabled(true);
  };

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
            <Progress percent={record.status} size="small" steps={10} strokeColor={blue[6]} style={{ width: 0, marginLeft: 3, fontSize: '10px' }} />
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
    onChange: (selectedRowKeys) => setSelectedModelKeys(selectedRowKeys.slice(-1)),
  };

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
        scroll={{ y: 200 }}
        onRow={(record, index) => ({
          ref: index === modelData.length - 1 ? ref : null,
        })}
        footer={() => (
          isFetchingNextPage ? <Spin indicator={<LoadingOutlined spin />} /> : null
        )}
      />
    </div>
  );
}

export default ModelTableSection;
