import React, { useState } from 'react';
import { message, Modal, Select, Input } from 'antd';
import { createModel } from 'api/ml';
import { useModel, useDataset } from 'hooks';
const { Option } = Select;

const ModelCreateModal = ({ isModalVisible, setIsModalVisible, selectedDatasetKeys, setSelectedDatasetKeys, setModelPollEnabled }) => {
    const [selectedModel, setSelectedModel] = useState(null);
    const [customModelName, setCustomModelName] = useState('');
    const { modelData } = useModel();
    const { datasetData } = useDataset();

    return (
        <Modal
            title={<span style={{ fontSize: '13px' }}>모델 생성</span>}
            open={isModalVisible}
            onOk={async () => {
                if (!customModelName) {
                    message.warning('모델 이름을 입력하세요.');
                    return;
                }

                if (!selectedModel) {
                    message.warning('기반 모델을 선택하세요.');
                    return;
                }

                if (customModelName.trim() === selectedModel.trim()) {
                    message.warning('기반 모델과 동일한 이름으로 설정할 수 없습니다.');
                    return;
                }

                setSelectedDatasetKeys([]);

                await createModel({ modelName: customModelName, baseModelName: selectedModel, zipFileIds: selectedDatasetKeys });
                
                setIsModalVisible(false);
                setSelectedModel(null);
                setCustomModelName('');

                setModelPollEnabled(true);
            }}
            onCancel={() => {
                setIsModalVisible(false);
                setSelectedModel(null);
                setCustomModelName('');
            }}
            okText="모델 생성"
            cancelText="취소"
            okButtonProps={{ style: { fontSize: '12px', height: '25px', borderRadius: '3px' } }}
            cancelButtonProps={{ style: { fontSize: '12px', height: '25px', borderRadius: '3px' } }}
        >
            <Input
                placeholder="모델 이름을 입력하세요"
                style={{ width: '100%', height: '30px', marginBottom: '10px' }}
                value={customModelName}
                onChange={(e) => setCustomModelName(e.target.value)}
            />

            <Select
                placeholder="기반 모델을 선택하세요"
                style={{ width: '100%', height: '30px', borderRadius: '3px' }}
                value={selectedModel}
                onChange={(value) => setSelectedModel(value)}
            >
                {modelData.filter((model) => model.status === 'complete').map((model) => (
                    <Option key={model.key} value={model.modelName}>
                        {model.modelName}
                    </Option>
                ))}
            </Select>

            <div style={{ marginTop: '10px' }}>
                <span style={{ fontSize: '12px', fontWeight: 'bold' }}>선택된 파일 목록:</span>
                <ul style={{ paddingLeft: '20px', fontSize: '12px', marginTop: '5px' }}>
                    {selectedDatasetKeys.map((datasetId, index) => {
                        const dataset = datasetData.find(dataset => dataset.key === datasetId)
                        return <li key={index}>{dataset.fileName}</li>
                    })}
                </ul>
            </div>
        </Modal>
    );
}

export default ModelCreateModal;
