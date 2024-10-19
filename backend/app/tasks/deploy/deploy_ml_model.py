import os
import shutil
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def deploy_to_triton(model_name: str, onnx_model_path: str, triton_model_repo: str):
    """
    Triton 서버에 ONNX 모델 배포
    """
    try:
        # Triton 모델 경로 설정 (예: 모델 저장소 안의 폴더 구조)
        model_version = '1'
        triton_model_path = os.path.join(triton_model_repo, model_name, model_version)

        # 모델 디렉터리 생성
        os.makedirs(triton_model_path, exist_ok=True)

        # ONNX 모델 파일을 Triton 서버 모델 저장소로 복사
        shutil.copy(onnx_model_path, triton_model_path)

        # Triton 서버용 config.pbtxt 생성
        create_triton_config(model_name, triton_model_path)

        logging.info(f"Model deployed to Triton model repo: {triton_model_path}")
        return triton_model_path

    except Exception as e:
        logging.error(f"Error deploying model to Triton: {e}")
        raise

def create_triton_config(model_name: str, model_path: str):
    """
    Triton 서버용 config.pbtxt 파일 생성
    """
    config_path = os.path.join(model_path, "config.pbtxt")
    config_content = f"""
name: "{model_name}"
platform: "onnxruntime_onnx"
max_batch_size: 1
input [
  {{
    name: "images"
    data_type: TYPE_FP32
    dims: [ 1, 3, 640, 640 ]
  }}
]
output [
  {{
    name: "output"
    data_type: TYPE_FP32
    dims: [ 1, 8400, 85 ]
  }}
]
"""

    with open(config_path, "w") as f:
        f.write(config_content)

    logging.info(f"Created Triton config.pbtxt at {config_path}")