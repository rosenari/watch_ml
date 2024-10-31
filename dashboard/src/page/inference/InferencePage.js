import React, {useCallback} from 'react';
import InferenceSection from 'page/inference/sections/InferenceSection';
import { useExecuteRepeat, useInference } from 'hooks';
import { loadInferenceList, pollInferenceStatus } from 'reloader';
import './InferencePage.css';

function InferencePage() {
  const { setInferenceData, state } = useInference();
  const { executeRepeat, stopExecution } = useExecuteRepeat();

  const startInferencePolling = useCallback(() => {
    executeRepeat(() => pollInferenceStatus(setInferenceData, stopExecution, state), 500);
  }, [executeRepeat, setInferenceData, stopExecution, state]);

  const reloadInferenceList = useCallback(() => {
    loadInferenceList(setInferenceData, startInferencePolling, stopExecution);
  }, [setInferenceData, startInferencePolling, stopExecution]);

  return (
    <div className="inference-page">
      <InferenceSection reloadInferenceList={reloadInferenceList} />
    </div>
  );
}

export default InferencePage;
