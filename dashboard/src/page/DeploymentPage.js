import React, { useState, useEffect, useCallback } from 'react';
import { Upload, Table, Button, message } from 'antd';
import { InboxOutlined, CheckOutlined, LoadingOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import { fileUpload, getFileList, deleteFile, validFiles, getValidFiles } from '../api/files';
import { useExecuteRepeat } from '../hooks/execute';
import { Spin } from 'antd';
import './DeploymentPage.css';  // 스타일 추가

const { Dragger } = Upload;

function DeploymentPage() {
  const [datasetData, setDatasetData] = useState([]); // 데이터셋 테이블의 데이터
  const [selectedDatasetKeys, setSelectedDatasetKeys] = useState([]); // 데이터셋 체크 박스 선택시 갱신
  const [modelData, setModelData] = useState([
    /*{
      key: '1',
      modelVersion: '1.0',
      precision: '45',
      recall: '10',
      map50: '1',
      map95: '1',
      creationDate: '2024-01-01',
      dataCount: 100,
      checked: false,
      current: true,
    },*/
  ]);
  const [fileList, setFileList] = useState([]); 
  const [validDatasetData, setValidDatasetData] = useState([]); // 파일 검사 상태 [{ file_name: ..., status: .... }]
  const { executeRepeat, stopExecution } = useExecuteRepeat();
  const [selectedModelKeys, setSelectedModelKeys] = useState([]); // 모델 체크 박스 선택시 갱신

  const reloadFileList = useCallback(async () => {
    try {
      const list = await getFileList();
      const validDatasetDataMap = validDatasetData.reduce((acc, { file_name, status }) => {
        acc[file_name] = status;
        return acc;
      }, {});

      const formatted_list = list.map((file, i) => {
        return {
          key: file.file_name,
          fileName: file.file_name,
          uploadDate: file.creation_date,
          fileSize: file.file_size,
          valid: (file.file_name in validDatasetDataMap) ? validDatasetDataMap[file.file_name] : ''
        }
      });
    
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

  // 파일 업로드 처리
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

  // 파일 리스트 초기화
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
        if (result === true) {
          message.success(`${fileName} 삭제 성공`);
        } else {
          message.error(`${fileName} 삭제 실패`);
        }
      } catch (error) {
        message.error(`${fileName} 삭제 실패`);
      }
    }

    reloadFileList();
  }

  const handleValid = async () => {
    if (selectedDatasetKeys.length === 0) {
      message.warning('검사할 파일을 지정하지 않았습니다.');
    }

    validFiles(selectedDatasetKeys); // 파일 검사 요청
    setSelectedDatasetKeys([]);
    startValidFilesPolling();
  }

  // 업로드 파일 선택 후 일시적으로 저장 (업로드 버튼을 눌렀을 때만 업로드)
  const uploadProps = {
    beforeUpload: (file) => {
      setFileList(prevList => [...prevList, file]);
      return false; 
    },
    fileList,
    onRemove: (file) => {
      setFileList(prevList => prevList.filter(item => item.uid !== file.uid)); // 파일 제거 처리
    },
  };

  // 데이터셋 테이블의 컬럼 정의
  const datasetColumns = [
    {
      title: '파일 이름',
      dataIndex: 'fileName',
      key: 'fileName',
      render: (text, record) => {
        return (
        <div>
          <span style={{ marginRight: '8px' }}>{text}</span>
          {record.valid === 'complete' && <CheckOutlined style={{ color: 'green', marginRight: 8 }} />}
          {record.valid === 'failed' && <ExclamationCircleOutlined style={{ color: 'red', marginRight: 8 }} />}
          {(record.valid === 'running' || record.valid === 'pending') && <Spin indicator={<LoadingOutlined spin />} size="small" />}
        </div>
        );
      }
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
    }
  ];

  // 모델 테이블의 컬럼 정의
  const modelColumns = [
    {
      title: '모델 버전',
      dataIndex: 'modelVersion',
      key: 'modelVersion',
      render: (text, record) => (
      <span>
        {record.current ? <CheckOutlined style={{ color: 'green', marginRight: 8 }} /> : null}
        {text}
      </span>
      ),
    },
    {
      title: "정밀도",
      dataIndex: 'precision',
      key: 'precision',
    },
      {
      title: "재현율",
      dataIndex: 'recall',
      key: 'recall',
    },
      {
      title: "mAP@0.5",
      dataIndex: 'map50',
      key: 'map50',
    },
      {
      title: "mAP@0.5:0.95",
      dataIndex: 'map95',
      key: 'map95',
    },
      {
      title: '생성 날짜',
      dataIndex: 'creationDate',
      key: 'creationDate',
    },
  ];

  // 데이터셋 테이블의 rowSelection (행별 체크박스)
  const datasetRowSelection = {
    selectedRowKeys: selectedDatasetKeys,
    onChange: (selectedRowKeys) => {
      setSelectedDatasetKeys(selectedRowKeys); // 선택된 행 업데이트
    },
  };

  // 모델 테이블의 rowSelection (행별 체크박스)
  const modelRowSelection = {
    selectedRowKeys: selectedModelKeys,
    onChange: (selectedRowKeys) => {
      setSelectedModelKeys(selectedRowKeys); // 선택된 행 업데이트
    },
    getCheckboxProps: (record) => ({
      disabled: record.current, // 현재 배포된 모델은 선택 불가
    }),
  };

  return (
    <div className="deplayment-page"> {/* 클래스 추가 */}
      <Dragger {...uploadProps} style={{ marginBottom: '20px' }}>
        <p className="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p className="ant-upload-text">데이터셋 아카이브를 업로드하세요 (zip)</p>
      </Dragger>

      {/* 업로드 및 초기화 버튼을 오른쪽으로 배치 */}
      <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '20px' }}>
        <Button className="upload-button" size="small" type="default" onClick={handleUpload} style={{ marginRight: '5px' }}>
          업로드
        </Button>
          <Button className="reset-button" size="small" type="default" onClick={handleReset}>
          초기화
        </Button>
      </div>

      {/* 데이터셋 테이블 */}
      <div style={{ marginBottom: '20px' }}>
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
          <h3 className="table-title">데이터셋</h3>
          <div>
            <Button type="default" size="small" className="table-button" style={{ marginRight: '5px' }} onClick={handleValid}>파일검사</Button>
            <Button type="default" size="small" className="table-button" style={{ marginRight: '5px' }}>모델생성</Button>
            <Button type="default" size="small" className="table-button" onClick={handleDelete}>파일삭제</Button>
          </div>
        </div>
        <Table
            className="custom-table" // 클래스 추가
            rowSelection={datasetRowSelection} // rowSelection 추가
            columns={datasetColumns}
            dataSource={datasetData}
            locale={{emptyText: '목록 없음'}}
            pagination={false}
        />
      </div>

      {/* 모델 테이블 */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <h3 className="table-title">모델</h3>
          <Button type="default" size="small" className="table-button">배포</Button>
        </div>
        <Table
          className="custom-table" // 클래스 추가
          rowSelection={modelRowSelection} // rowSelection 추가
          columns={modelColumns}
          dataSource={modelData}
          locale={{ emptyText: '목록 없음' }}
          pagination={false}
        />
      </div>

    </div>
  );
}

export default DeploymentPage;
