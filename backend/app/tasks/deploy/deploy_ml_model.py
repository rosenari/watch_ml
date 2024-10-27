import os
import shutil
import logging


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# Triton 서버에 모델 배포
def deploy_to_triton(model_name: str, version: int, model_path: str, triton_model_repo: str, triton_server_url: str):
    try:
        from ultralytics import YOLO

        triton_model_path = os.path.join(triton_model_repo, model_name)
        version_path = os.path.join(triton_model_path, str(version))
        dest_path = os.path.join(version_path, f"model.onnx") 

        os.makedirs(version_path, exist_ok=True)

        ## export 로직 필요. onnx로 변환
        model = YOLO(model_path)
        onnx_model_path = model.export(format="onnx", dynamic=True, simplify=True)

        shutil.copy(onnx_model_path, dest_path)
        output_dims = extract_output_dims(onnx_model_path)

        create_triton_config(model_name, triton_model_path, output_dims)  # 설정파일은 버전 디렉터리와 같은 위치에 생성

        logging.info(f"Model moved to Triton model repo: {version_path}")

        # Triton 서버에 모델 로드 요청
        if load_model_to_triton(triton_server_url, model_name):
            logging.info(f"Model {model_name} successfully loaded to Triton server.")
            return True, dest_path
        else:
            logging.error(f"Failed to load model {model_name} to Triton server.")
            return False, None

    except Exception as e:
        logging.error(f"Error deploying model to Triton: {e}")
        return False, None


# Triton 서버용 config.pbtxt 파일 생성
def create_triton_config(model_name: str, model_path: str, output_dims: list):
    config_path = os.path.join(model_path, "config.pbtxt")

    if output_dims[0] == -1:
        output_dims = output_dims[1:]
    
    output_dims_str = ', '.join(map(str, output_dims))
    
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
    name: "output0"
    data_type: TYPE_FP32
    dims: [ {output_dims_str} ]
  }}
]
"""

    with open(config_path, "w") as f:
        f.write(config_content)

    logging.info(f"Created Triton config.pbtxt at {config_path}")

  
# gRPC를 통해 Triton 서버에 모델 로드 요청
def load_model_to_triton(triton_server_url: str, model_name: str):
    try:
        import tritonclient.grpc as trtgrpc
        triton_client = trtgrpc.InferenceServerClient(url=triton_server_url)

        # 모델을 명시적으로 로드하기 위한 gRPC 요청
        triton_client.load_model(model_name)
        logging.info(f"Requested loading of model {model_name} on Triton server.")
        return True

    except Exception as e:
        logging.error(f"Error loading model to Triton: {e}")
        return False
    

def extract_output_dims(onnx_model_path: str):
    import onnx
    model = onnx.load(onnx_model_path)
    output_dims = []
    for output in model.graph.output:
        dims = [dim.dim_value if dim.dim_value > 0 else -1 for dim in output.type.tensor_type.shape.dim]
        output_dims.append(dims)
    return output_dims[0]  # 첫 번째 출력 텐서의 차원을 반환