export const formatDatasetList = (datasetList) => {
    return datasetList.map((dataset) => ({
        key: dataset.id,
        fileName: dataset.file_name,
        fileSize: dataset.file_meta ? dataset.file_meta.filesize : '-',
        uploadDate: dataset.file_meta ? dataset.file_meta.creation_time : '-',
        status: dataset.status
    }));
}



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