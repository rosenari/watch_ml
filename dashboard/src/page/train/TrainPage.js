import React, { useState } from 'react';
import DatasetSection from 'page/train/sections/DatasetSection';
import ModelTableSection from 'page/train/sections/ModelSection';
import './TrainPage.css';

function TrainPage() {
  const [modelPollEnabled, setModelPollEnabled] = useState(true);

  return (
    <div className="deplayment-page">
      <DatasetSection setModelPollEnabled={setModelPollEnabled} />
      <ModelTableSection modelPollEnabled={modelPollEnabled} setModelPollEnabled={setModelPollEnabled} />
    </div>
  );
}

export default TrainPage;
