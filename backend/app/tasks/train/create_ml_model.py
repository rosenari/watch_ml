import os
import logging
import traceback


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def create_yolo_model(model_name: str, output_dir: str, ml_runs_path: str, status_handler=lambda ri_key, status: None):
    logging.info("start create_yolo_model")
    # celery와 fastapi 의존성 분리로 인해 함수내에서 패키지 로딩
    import mlflow
    from ultralytics import YOLO

    epochs = 10
    img_size = 640

    # data.yaml 파일 경로 설정
    data_yaml = os.path.join(output_dir, "data.yaml")
    
    # YOLOv8 모델 객체 생성
    model = YOLO('yolov8s.pt')

    def on_train_epoch_end(trainer):
        epoch = trainer.epoch
        total_epochs = trainer.epochs
        logging.info(f"Epoch {epoch + 1}/{total_epochs} completed")
        status_handler(f"model:{model_name}", f"Epoch {epoch + 1} completed")


    try:
        model.add_callback("on_train_epoch_end", on_train_epoch_end)

        model.train(
            data=data_yaml, 
            epochs=epochs,  
            imgsz=img_size,
            device='cuda:0',
        )

        model.export(format="onnx", imgsz=img_size, dynamic=True, simplify=True)

        artifact_path = model_name
        #mlflow.log_artifact(onnx_model_path, artifact_path=artifact_path)

        # 모델 레지스트리에 등록
        """
        mlflow.pyfunc.log_model(
            artifact_path=artifact_path,
            python_model=None,  
            registered_model_name=model_name
        )
        """

        # 학습 완료 상태를 Redis에 기록
        status_handler(f"model:{model_name}", "complete")

        logging.info(f"YOLOv8 model has been successfully registered in MLflow")
        return True
    
    except Exception as e:
        status_handler(f"model:{model_name}", "failed")
        logging.error(f"An error occurred while creating and saving the model: {e}")
        logging.error(traceback.format_exc())
        return False
