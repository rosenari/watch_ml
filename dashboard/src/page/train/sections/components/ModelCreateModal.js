
import React, { useState } from 'react';
import { message, Modal, Select } from 'antd';
const { Option } = Select;

const ModelCreateModal = ({ modelData, isModalVisible, setIsModalVisible, selectedDatasetKeys, setSelectedDatasetKeys }) => {
    const [selectedModel, setSelectedModel] = useState(null);

    return (
        <Modal
        title={<span style={{ fontSize: '13px' }}>모델 생성</span>}
        open={isModalVisible}
        onOk={() => {
          if (!selectedModel) {
            message.warning('기반 모델을 선택하세요.');
            return;
          }
          setIsModalVisible(false);
          setSelectedModel(null);
          setSelectedDatasetKeys([]);
        }}
        onCancel={() => {
          setIsModalVisible(false);
          setSelectedModel(null);
        }}
        okText="모델 생성"
        cancelText="취소"
        okButtonProps={{ style: { fontSize: '12px', height: '25px', borderRadius: '3px' } }}
        cancelButtonProps={{ style: { fontSize: '12px', height: '25px', borderRadius: '3px' } }}
      >
        <Select
          placeholder="기반 모델을 선택하세요"
          style={{ width: '100%', height: '30px', borderRadius: '3px' }} // Select 크기 조정
          value={selectedModel}
          onChange={(value) => setSelectedModel(value)}
        >
            {modelData.map((model) => (
                <Option key={model.key} value={model.modelName}>
                    {model.modelName}
                </Option>
            ))}
        </Select>

        <div style={{ marginTop: '10px' }}>
          <span style={{ fontSize: '12px', fontWeight: 'bold' }}>선택된 파일 목록:</span>
          <ul style={{ paddingLeft: '20px', fontSize: '12px', marginTop: '5px' }}>
            {selectedDatasetKeys.map((fileName, index) => (
              <li key={index}>{fileName}</li>
            ))}
          </ul>
        </div>
      </Modal>
    );
}

export default ModelCreateModal;