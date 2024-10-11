import React, { useState } from 'react';
import { Upload, Table, Button, message } from 'antd';
import { InboxOutlined, CheckCircleOutlined } from '@ant-design/icons';
import './DeploymentPage.css';  // 스타일 추가

const { Dragger } = Upload;

function DeploymentPage() {
  const [datasetData, setDatasetData] = useState([]); // 데이터셋 테이블의 데이터
  const [selectedDatasetKeys, setSelectedDatasetKeys] = useState([]); // 데이터셋 테이블의 선택된 행
  const [modelData, setModelData] = useState([
    {
      key: '1',
      modelVersion: '1.0',
      creationDate: '2024-01-01',
      dataCount: 100,
      checked: false,
      current: true,
    },
  ]); // 모델 테이블의 데이터
  const [selectedModelKeys, setSelectedModelKeys] = useState([]); // 모델 테이블의 선택된 행
  const [fileList, setFileList] = useState([]); // 선택된 파일들을 저장할 상태

  // 파일 업로드 처리
  const handleUpload = () => {
    // 업로드할 파일이 없을 경우 메시지 출력
    if (fileList.length === 0) {
      message.error('업로드할 파일이 없습니다.');
      return;
    }

    // 각 파일을 처리하는 로직 (서버로 업로드하는 실제 처리)
    fileList.forEach((file) => {
      const formData = new FormData();
      formData.append('file', file);

      // 실제 업로드 요청 (서버 경로에 맞게 변경 필요)
      fetch('/upload.do', {
        method: 'POST',
        body: formData,
      })
      .then(response => response.json())
      .then(data => {
        message.success(`${file.name} 업로드 성공`);

        // 데이터셋 테이블에 업로드된 파일 정보 추가
        setDatasetData(prevData => [
          ...prevData,
          {
            key: file.uid,
            fileName: file.name,
            uploadDate: new Date().toLocaleString(),
          },
        ]);
      })
      .catch(() => {
        message.error(`${file.name} 업로드 실패`);
      });
    });

    // 업로드 후 파일 목록 초기화
    setFileList([]);
  };

  // 파일 리스트 초기화
  const handleReset = () => {
    setFileList([]); // 파일 리스트 초기화
    message.success('파일 목록이 초기화되었습니다.');
  };

  // 업로드 파일 선택 후 일시적으로 저장 (업로드 버튼을 눌렀을 때만 업로드)
  const uploadProps = {
    beforeUpload: (file) => {
      setFileList(prevList => [...prevList, file]);
      return false; // 자동 업로드 방지
    },
    fileList, // 현재 선택된 파일 목록 표시
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
    },
    {
      title: '업로드 날짜',
      dataIndex: 'uploadDate',
      key: 'uploadDate',
      width: 300,
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
        {record.current ? <CheckCircleOutlined style={{ color: 'green', marginRight: 8 }} /> : null}
        {text}
      </span>
    ),
    },
      {
      title: '생성 날짜',
      dataIndex: 'creationDate',
      key: 'creationDate',
      width: 300,
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
        <p className="ant-upload-text">데이터셋 파일을 업로드하세요</p>
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
            <Button type="default" size="small" className="table-button" style={{ marginRight: '5px' }}>모델생성</Button>
            <Button type="default" size="small" className="table-button">파일삭제</Button>
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
