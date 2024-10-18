import os
import mlflow
from ultralytics import YOLO
import logging


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def create_yolo_model(model_name: str, output_dir: str, status_handler=lambda ri_key, status: None):
    epochs = 100
    img_size = 640

    # data.yaml 파일 경로 설정
    data_yaml = os.path.join(output_dir, "data.yaml")
    
    # YOLOv8 모델 객체 생성
    model = YOLO(model_name)

    try:
        with mlflow.start_run() as run:

            for epoch in range(epochs):
                status_handler(f"model:{model_name}", f"{epoch + 1}")

                model.train(
                    data=data_yaml, 
                    epochs=1,          
                    imgsz=img_size,
                    resume=True  # 이전 에포크에서 이어서 학습
                )

                logging.info(f"[create_yolo_model] epoch: {epoch + 1}/{epochs}")
            
            trained_model_path = os.path.join("runs", "train", "weights", "best.pt")

            onnx_model_path = os.path.join(output_dir, f"{model_name}.onnx")
            model.export(format="onnx", imgsz=img_size, weights=trained_model_path, path=onnx_model_path)

            artifact_path = model_name
            mlflow.log_artifact(onnx_model_path, artifact_path=artifact_path)

            # 모델 레지스트리에 등록
            mlflow.pyfunc.log_model(
                artifact_path=artifact_path,
                python_model=None,  
                registered_model_name=model_name
            )

            # 학습 완료 상태를 Redis에 기록
            status_handler(f"model:{model_name}", "complete")

            logging.info(f"YOLOv8 model has been successfully registered in MLflow: {onnx_model_path}")
            return True
    
    except Exception as e:
        status_handler(f"model:{model_name}", "failed")
        logging.error(f"An error occurred while creating and saving the model: {e}")
        return False
