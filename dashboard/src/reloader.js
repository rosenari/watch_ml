
import { getDatasetList, getDatasetStatus } from 'api/dataset';
import { getModelList, getModelStatus } from 'api/ml';
import { getInferenceList, getInferenceStatus } from 'api/inference';

export const formatModelList = (modelList) => {
    return modelList.map((model) => ({
        key: model.id,
        modelName: model.model_name,
        version: model.version,
        map50: model.map50 ? Number(model.map50).toFixed(2) : '-',
        map50_95: model.map50_95 ?  Number(model.map50_95).toFixed(2) : '-',
        precision: model.precision ? Number(model.precision).toFixed(2) : '-',
        recall: model.recall ? Number(model.recall).toFixed(2) : '-',
        classes: model.classes ?? '-',
        status: model.status,
        isDeploy: model.is_deploy ? '🚀' : '-',
        baseModelName: model.base_model ? model.base_model.model_name : '-'
    }));
}

export const loadDatasetList = async (setDatasetData, startPolling, stopExecution) => {
  try {
    const datasetList = await getDatasetList();
    const formattedList = datasetList.map((dataset) => ({
      key: dataset.id,
      fileName: dataset.file_name,
      uploadDate: dataset.file_meta.creation_time,
      fileSize: dataset.file_meta.filesize,
      status: dataset.status,
    }));

    setDatasetData(formattedList);

    const hasRunningItems = datasetList.some(
      (dataset) => dataset.status === 'running' || dataset.status === 'pending'
    );

    if (hasRunningItems) {
      startPolling();
    }
  } catch (error) {
    console.error(`Failed to load file list: ${error}`);
    stopExecution();
  }
};


export const pollDatasetStatus = async (setDatasetData, stopExecution, state) => {
  const validFiles = await getDatasetStatus();
  const updatedDataset = state.dataset.map((dataset) => {
    const fileStatus = validFiles.find((file) => file.file_name === dataset.fileName);
    return {
      ...dataset,
      status: fileStatus ? fileStatus.status : dataset.status,
    };
  });

  setDatasetData(updatedDataset);

  const hasRunningItems = updatedDataset.some(
    (dataset) => dataset.status === 'running' || dataset.status === 'pending'
  );

  if (!hasRunningItems) {
    stopExecution();
  }
};


export const loadModelList = async (setModelData, startPolling, stopExecution) => {
  try {
    const modelList = await getModelList();
    const formattedList = formatModelList(modelList);

    setModelData(formattedList);

    const hasRunningItems = modelList.some(
      (model) => model.status === 'running' || model.status === 'pending'
    );

    if (hasRunningItems) {
      startPolling();
    }
  } catch (error) {
    console.error(`Failed to load model list: ${error}`);
    stopExecution();
  }
};


export const pollModelStatus = async (setModelData, stopExecution, state) => {
    const modelStatus = await getModelStatus();
    const updatedModel = state.model.map((model) => {
      const newModelStatus = modelStatus.find((model_status) => model_status.model_name === model.modelName);
      return {
        ...model,
        status: newModelStatus ? newModelStatus.status : model.status,
      };
    });
  
    setModelData(updatedModel);
  
    const hasRunningItems = updatedModel.some(
      (model) => model.status === 'running' || model.status === 'pending' || /^\d+$/.test(model.status)
    );
  
    if (!hasRunningItems) {
      stopExecution();
      const modelList = await getModelList();
      const formattedList = formatModelList(modelList);

      setModelData(formattedList);
    }
  };

  
  export const formatInferenceList = (inferenceList) => {
    return inferenceList.map((inference) => ({
      key: inference.id,
      originalFileId: inference.original_file ? inference.original_file.id : '-',
      originalFileName: inference.original_file_name,
      originalFileSize: inference.original_file.filesize,
      generatedFileId: inference.generated_file ? inference.generated_file.id : '-',
      generatedFileName: inference.generated_file_name ?? '-',
      generatedFileSize: inference.generated_file ? inference.generated_file.filesize : '-',
      fileType: inference.file_type,
      status: inference.status,
  }));
  }


  export const loadInferenceList = async (setInferenceData, startPolling, stopExecution) => {
    try {
      const inferenceList = await getInferenceList();
      const formattedList = formatInferenceList(inferenceList);
  
      setInferenceData(formattedList);
  
      const hasRunningItems = inferenceList.some(
        (inference) => inference.status === 'running' || inference.status === 'pending'
      );
  
      if (hasRunningItems) {
        startPolling();
      }
    } catch (error) {
      console.error(`Failed to load inference list: ${error}`);
      stopExecution();
    }
  };
  
  
  export const pollInferenceStatus = async (setInferenceData, stopExecution, state) => {
      const inferenceStatus = await getInferenceStatus();
      const updatedInference = state.inference.map((inference) => {
        const newInferenceStatus = inferenceStatus.find((inference_status) => inference_status.original_file_name === inference.originalFileName);
        return {
          ...inference,
          status: newInferenceStatus ? newInferenceStatus.status : inference.status,
        };
      });
    
      setInferenceData(updatedInference);
    
      const hasRunningItems = updatedInference.some(
        (inference) => inference.status === 'running' || inference.status === 'pending'
      );
    
      if (!hasRunningItems) {
        stopExecution();
        const inferenceList = await getInferenceList();
        const formattedList = formatInferenceList(inferenceList);
  
        setInferenceData(formattedList);
      }
    };