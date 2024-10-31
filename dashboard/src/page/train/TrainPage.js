import React from 'react';
import DatasetSection from 'page/train/sections/DatasetSection';
import ModelTableSection from 'page/train/sections/ModelSection';
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
