import os
import logging
import traceback
import shutil


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def create_yolo_model(model_name: str, output_dir: str, ml_runs_path: str, status_handler=lambda ri_key, status: None):
    logging.info("start create_yolo_model")
    # celery와 fastapi 의존성 분리로 인해 함수내에서 패키지 로딩
    from ultralytics import YOLO

    epochs = 1
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

        export_path = model.export(format="onnx", imgsz=img_size, dynamic=True, simplify=True)
        logging.info(f"onnx model export path: {export_path}")

        # onnx 모델을 레포로 복사
        ML_REPO = 'model_repo'
        dest_path = os.path.join(ml_runs_path, ML_REPO, model_name)
        if not os.path.exists(dest_path):
            os.makedirs(dest_path, exist_ok=True)
        
        shutil.copy(export_path, dest_path)
        logging.info(f"YOLOv8 model has been successfully stored")

        clear_directory_except(ml_runs_path ,[ML_REPO, 'triton_repo'])  # 찌꺼기 제거
        return True
    except Exception as e:
        logging.error(f"An error occurred while creating and saving the model: {e}")
        logging.error(traceback.format_exc())
        return False
    

# 특정 디렉터리 내에서 제외할 디렉터리를 제외하고 모든 파일과 디렉터리를 삭제
def clear_directory_except(target_dir: str, exclude_dirs: list):
    for item in os.listdir(target_dir):
        item_path = os.path.join(target_dir, item)

        if item in exclude_dirs:
            continue
        
        if os.path.isdir(item_path):
            shutil.rmtree(item_path)
            logging.info(f"Directory removed: {item_path}")
        elif os.path.isfile(item_path):
            os.remove(item_path)
            logging.info(f"File removed: {item_path}")