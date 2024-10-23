import os
import shutil
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# Triton 서버에 모델 배포
def deploy_to_triton(model_name: str, version: int, onnx_model_path: str, triton_model_repo: str):
    try:
        triton_model_path = os.path.join(triton_model_repo, model_name)
        version_path = os.path.join(triton_model_path, version)

        os.makedirs(version_path, exist_ok=True)

        shutil.copy(onnx_model_path, version_path)

        create_triton_config(model_name, triton_model_path)  # 설정파일은 버전 디렉터리와 같은 위치에 생성

        logging.info(f"Model deployed to Triton model repo: {version_path}")
        return True

    except Exception as e:
        logging.error(f"Error deploying model to Triton: {e}")
        return False


# Triton 서버용 config.pbtxt 파일 생성
def create_triton_config(model_name: str, model_path: str):
    config_path = os.path.join(model_path, "config.pbtxt")
    config_content = f"""
name: "{model_name}"
platform: "onnxruntime_onnx"
max_batch_size: 10
input [
  {{
    name: "images"
    data_type: TYPE_FP32
    dims: [ 3, 640, 640 ]
  }}
]
output [
  {{
    name: "output"
    data_type: TYPE_FP32
    dims: [ 8400, 85 ]
  }}
]
"""

    with open(config_path, "w") as f:
        f.write(config_content)

    logging.info(f"Created Triton config.pbtxt at {config_path}")