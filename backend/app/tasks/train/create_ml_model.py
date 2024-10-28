import os
import logging
import traceback
import shutil


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def create_yolo_model(model_name: str, model_ext: str, base_model_path: str, version: int, output_dir: str, ml_runs_path: str, status_handler=lambda ri_key, status: None):
    logging.info("start create_yolo_model")
    # celery와 fastapi 의존성 분리로 인해 함수내에서 패키지 로딩 (yolo 패키지는 celery에만 존재)
    from ultralytics import YOLO
    import torch

    file_name = f"{model_name}.{model_ext}"
    ML_REPO = 'model_repo'
    TRITON_REPO = 'triton_repo'
    epochs = 100
    img_size = 640

    # data.yaml 파일 경로 설정
    data_yaml = os.path.join(output_dir, "data.yaml")
    
    # YOLOv8 모델 객체 생성
    model = YOLO(base_model_path)

    def on_train_epoch_end(trainer):
        epoch = trainer.epoch
        total_epochs = trainer.epochs
        logging.info(f"Epoch {epoch + 1}/{total_epochs} completed")
        status_handler(f"train:{model_name}", f"Epoch {epoch + 1} completed")


    try:
        model.add_callback("on_train_epoch_end", on_train_epoch_end)

        model.train(
            data=data_yaml, 
            epochs=epochs,  
            imgsz=img_size,
            batch=2,
            device='cuda:0',
        )

        metrics = model.val(
            data=data_yaml,
            imgsz=img_size,
            batch=2,
            device='cuda:0',
        )
        map50 = metrics.box.map50
        map50_95 = metrics.box.map
        precision = metrics.box.mp
        recall = metrics.box.mr

        best_model_path = model.best
        logging.info(f"best model path: {best_model_path}")

        # best 모델을 레포로 복사
        dest_path = os.path.join(ml_runs_path, ML_REPO, model_name, str(version))
        if not os.path.exists(dest_path):
            os.makedirs(dest_path, exist_ok=True)
        
        new_dest_path = os.path.join(dest_path, file_name)
        shutil.copy(best_model_path, new_dest_path)
        logging.info(f"YOLOv8 model has been successfully stored")
        
        return True, {
            "model_name": model_name,
            "version": version,
            "model_path": os.path.join(dest_path, file_name),
            "map50": map50,
            "map50_95": map50_95,
            "precision": precision,
            "recall": recall
        }
    except Exception as e:
        logging.error(f"An error occurred while creating and saving the model: {e}")
        logging.error(traceback.format_exc())
        return False, None
    finally:
        # 명시적으로 자원을 전부 해제한다.
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        del model 
        logging.info("Deleted YOLO model object to release memory.")
        
        clear_directory_except(ml_runs_path ,[ML_REPO, TRITON_REPO])  # 찌꺼기 제거
        logging.info("Temporary directories cleaned up.")
    

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