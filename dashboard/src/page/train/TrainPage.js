import React, {useCallback} from 'react';
import DatasetSection from 'page/train/sections/DatasetSection';
import ModelTableSection from 'page/train/sections/ModelSection';
import { useExecuteRepeat, useModel, useDataset } from 'hooks';
import { loadDatasetList, pollDatasetStatus, loadModelList, pollModelStatus } from './reloader';
import './TrainPage.css';

function TrainPage() {
  const { setModelData, state } = useModel();
  const { setDatasetData } = useDataset();
  const { executeRepeat, stopExecution } = useExecuteRepeat();

  const startDatasetPolling = useCallback(() => {
    executeRepeat(() => pollDatasetStatus(setDatasetData, stopExecution, state), 500);
  }, [executeRepeat, setDatasetData, stopExecution, state]);
  
  const reloadDatasetList = useCallback(() => {
    loadDatasetList(setDatasetData, startDatasetPolling, stopExecution);
  }, [setDatasetData, startDatasetPolling, stopExecution]);

  const startModelPolling = useCallback(() => {
    executeRepeat(() => pollModelStatus(setModelData, stopExecution, state), 500);
  }, [executeRepeat, setModelData, stopExecution, state]);

  const reloadModelList = useCallback(() => {
    loadModelList(setModelData, startModelPolling, stopExecution);
  }, [setModelData, startModelPolling, stopExecution]);

  return (
    <div className="deplayment-page">
      <DatasetSection reloadDatasetList={reloadDatasetList} reloadModelList={reloadModelList} />
      <ModelTableSection reloadModelList={reloadModelList} />
    </div>
  );
}

export default TrainPage;
