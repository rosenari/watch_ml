#!/bin/bash

DATASET_ID=$1

curl -X DELETE "http://localhost:5000/dataset/$DATASET_ID"