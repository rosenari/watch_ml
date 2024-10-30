// TrainPage.js

import React from 'react';
import DatasetSection from 'page/train/DatasetSection';
import ModelTableSection from 'page/train/ModelSection';
import './TrainPage.css';

function TrainPage() {
  return (
    <div className="deplayment-page">
      <DatasetSection />
      <ModelTableSection />
    </div>
  );
}

export default TrainPage;
