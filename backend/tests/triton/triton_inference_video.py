import os
import numpy as np
import cv2
from tqdm import tqdm
import tritonclient.grpc as grpcclient
from tritonclient.grpc import InferInput, InferRequestedOutput


def generate_primary_colors(num_colors):
    primary_colors = [
        (255, 0, 0),   # 빨강
        (0, 255, 0),   # 초록
        (0, 0, 255),   # 파랑
        (255, 255, 0), # 노랑
        (255, 0, 255), # 보라
        (0, 255, 255)  # 청록
    ]
    
    colors = []
    np.random.seed(0)  # 일관된 색상 출력을 위해 시드 설정
    for i in range(num_colors):
        base_color = primary_colors[i % len(primary_colors)]
        # 밝기 변화를 위한 양수 variation 적용
        variation = np.random.randint(0, 50, size=3) 
        color = tuple(max(0, min(255, base + var)) for base, var in zip(base_color, variation))
        colors.append(tuple(map(int, color)))  # 정수로 변환

    return colors



# 클래스 이름 설정
CLASSES = ["short_sleeved_shirt", "long_sleeved_shirt", "short_sleeved_outwear", "long_sleeved_outwear", "vest", "sling", 
           "shorts", "trousers", "skirt", "short_sleeved_dress", "long_sleeved_dress", "vest_dress", "sling_dress"]

# 클래스별 고정 색상 설정
colors = generate_primary_colors(len(CLASSES))

# Triton 서버 설정
triton_url = "localhost:8001"
model_name = "fashion_model"
input_name = "images"
output_name = "output0"
triton_client = grpcclient.InferenceServerClient(url=triton_url)

def draw_bounding_box(img, class_id, confidence, x, y, x_plus_w, y_plus_h):
    label = f"{CLASSES[class_id]} ({confidence:.2f})"
    color = colors[class_id % len(colors)]  # 클래스 인덱스를 기반으로 고정된 색상 선택
    cv2.rectangle(img, (int(x), int(y)), (int(x_plus_w), int(y_plus_h)), color, 2)
    cv2.putText(img, label, (int(x), int(y) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

def process_frame(frame):
    # BGR -> RGB 변환
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # 원본 크기 저장 및 리사이즈
    original_height, original_width = frame_rgb.shape[:2]
    resized_frame = cv2.resize(frame_rgb, (640, 640))
    image = resized_frame.astype(np.float32) / 255.0
    image = np.transpose(image, (2, 0, 1))
    image = np.expand_dims(image, axis=0)

    # Triton 입력 및 출력 설정
    inputs = [InferInput(input_name, image.shape, "FP32")]
    inputs[0].set_data_from_numpy(image)
    outputs = [InferRequestedOutput(output_name)]
    response = triton_client.infer(model_name=model_name, inputs=inputs, outputs=outputs)
    output_data = response.as_numpy(output_name)[0]

    confidence_threshold = 0.3
    nms_threshold = 0.4
    boxes, scores, class_ids = [], [], []
    x_scale, y_scale = original_width / 640, original_height / 640

    for detection in output_data:
        x_min, y_min, x_max, y_max, confidence, class_id = detection[:6]
        class_id = int(class_id)

        if confidence >= confidence_threshold:
            x_min, y_min = int(x_min * x_scale), int(y_min * y_scale)
            x_max, y_max = int(x_max * x_scale), int(y_max * y_scale)
            boxes.append([x_min, y_min, x_max - x_min, y_max - y_min])
            scores.append(float(confidence))
            class_ids.append(class_id)

    indices = cv2.dnn.NMSBoxes(boxes, scores, confidence_threshold, nms_threshold)
    if len(indices) > 0:
        for i in indices.flatten():
            box = boxes[i]
            x, y, w, h = box
            draw_bounding_box(frame_rgb, class_ids[i], scores[i], x, y, x + w, y + h)

    # RGB -> BGR 변환하여 반환
    return cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

def infer_video(input_video_path, output_video_path):
    cap = cv2.VideoCapture(input_video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video {input_video_path}")
        return

    # 프레임 속성 가져오기
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # VideoWriter 객체 생성
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

    with tqdm(total=total_frames, desc="Processing Video", unit="frame") as pbar:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # 프레임 처리
            processed_frame = process_frame(frame)
            out.write(processed_frame)
            pbar.update(1)

    # 자원 해제
    cap.release()
    out.release()

    print(f"Video with bounding boxes saved at {output_video_path}")

input_video_path = "./mock/runway.mp4"
output_dir = 'detection_results'

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

output_video_path = os.path.join(output_dir, "detection_runway_no_audio.mp4")
infer_video(input_video_path, output_video_path)
