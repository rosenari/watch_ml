#!/bin/bash

INFERENCE_ID=$1

curl -X DELETE "http://localhost:5000/inference/$INFERENCE_ID"