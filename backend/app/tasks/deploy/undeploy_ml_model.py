import os
import shutil
import logging



logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# Triton 서버에서 모델 언로드
def undeploy_from_triton(model_name: str, triton_model_repo: str, triton_server_url: str):
    try:
        import tritonclient.grpc as trtgrpc
        triton_client = trtgrpc.InferenceServerClient(url=triton_server_url)

        # 모델 언로드 요청
        triton_client.unload_model(model_name)
        logging.info(f"Requested unloading of model {model_name} on Triton server.")

        # 모델 디렉터리 제거
        triton_model_path = os.path.join(triton_model_repo, model_name)
        shutil.rmtree(triton_model_path)
        logging.info(f"Model directory removed: {triton_model_path}")

        return True

    except Exception as e:
        logging.error(f"Error undeploying model from Triton: {e}")
        return False
  