import { modelAtom, datasetAtom, inferenceAtom } from 'store';
import { useAtom } from 'jotai';


export function useModel() {
    const [modelData, setModelData]  = useAtom(modelAtom);
    return {modelData, setModelData};
}


export function useDataset() {
    const [datasetData, setDatasetData]  = useAtom(datasetAtom);
    return {datasetData, setDatasetData};
}


export function useInference() {
    const [inferenceData, setInferenceData] = useAtom(inferenceAtom);
    return {inferenceData, setInferenceData};
}