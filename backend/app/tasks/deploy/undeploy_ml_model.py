import os
import shutil
import logging
from app.logger import LOGGER_NAME



logger = logging.getLogger(LOGGER_NAME)


# Triton 서버에서 모델 언로드
def undeploy_from_triton(model_name: str, triton_model_repo: str, triton_server_url: str):
    try:
        import tritonclient.grpc as trtgrpc
        triton_client = trtgrpc.InferenceServerClient(url=triton_server_url)

        # 모델 언로드 요청
        triton_client.unload_model(model_name)
        logger.info(f"Requested unloading of model {model_name} on Triton server.")

        # 모델 디렉터리 제거
        triton_model_path = os.path.join(triton_model_repo, model_name)
        shutil.rmtree(triton_model_path)
        logger.info(f"Model directory removed: {triton_model_path}")

        return True

    except Exception as e:
        logger.error(f"Error undeploying model from Triton", exc_info=True)
        return False
  