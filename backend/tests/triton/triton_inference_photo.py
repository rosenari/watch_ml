import os
import numpy as np
import cv2
import tritonclient.grpc as grpcclient
from tritonclient.grpc import InferInput, InferRequestedOutput

# 클래스 이름 설정
CLASSES = ["short_sleeved_shirt", "long_sleeved_shirt", "short_sleeved_outwear", "long_sleeved_outwear", "vest", "sling", 
           "shorts", "trousers", "skirt", "short_sleeved_dress", "long_sleeved_dress", "vest_dress", "sling_dress"]

# 색상 설정
colors = np.random.uniform(0, 255, size=(len(CLASSES), 3))

def draw_bounding_box(img, class_id, confidence, x, y, x_plus_w, y_plus_h):
    label = f"{CLASSES[class_id]} ({confidence:.2f})"
    color = colors[class_id]
    cv2.rectangle(img, (int(x), int(y)), (int(x_plus_w), int(y_plus_h)), color, 2)
    cv2.putText(img, label, (int(x), int(y) - 10), cv2.FONT_HERSHEY_PLAIN, 1.8, color, 2)

def main():
    # Triton 서버 설정
    triton_url = "localhost:8001"
    model_name = "fashion_model"
    input_name = "images"
    output_name = "output0"

    # 이미지 경로 및 저장 경로
    image_name = "f_runway.png" # junghoyeon_runway.png, junghoyeon_runway2.png
    image_path = f"./mock/{image_name}"
    output_dir = "./detection_results"
    output_path = os.path.join(output_dir, f"detection_{image_name}")

    # 결과 폴더가 없으면 생성
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 입력 이미지 읽기
    original_image = cv2.imread(image_path)
    if original_image is None:
        print(f"Error: Could not read image {image_path}")
        return
    
    original_image = cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB)

    # 원본 크기 저장 및 리사이즈
    original_height, original_width = original_image.shape[:2]
    resized_image = cv2.resize(original_image, (640, 640))
    image = resized_image.astype(np.float32) / 255.0
    image = np.transpose(image, (2, 0, 1))  # HWC -> CHW
    image = np.expand_dims(image, axis=0)  # 배치 차원 추가

    # Triton gRPC 클라이언트 생성
    triton_client = grpcclient.InferenceServerClient(url=triton_url)

    # 입력 데이터 설정
    inputs = [InferInput(input_name, image.shape, "FP32")]
    inputs[0].set_data_from_numpy(image)

    # 출력 데이터 설정
    outputs = [InferRequestedOutput(output_name)]

    # 추론 실행
    response = triton_client.infer(model_name=model_name, inputs=inputs, outputs=outputs)
    output_data = response.as_numpy(output_name)[0]

    # 신뢰도 및 NMS 임계값 설정
    confidence_threshold = 0.1
    nms_threshold = 0.5

    # 바운딩 박스 그리기
    boxes = []
    scores = []
    class_ids = []

    # 스케일 비율 계산
    x_scale = original_width / 640
    y_scale = original_height / 640

    for detection in output_data:
        x_min, y_min, x_max, y_max, confidence, class_id = detection[:6]
        class_id = int(class_id)

        if confidence >= confidence_threshold:
            # 좌표 변환을 원본 크기에 맞춰 조정
            x_min = int(x_min * x_scale)
            y_min = int(y_min * y_scale)
            x_max = int(x_max * x_scale)
            y_max = int(y_max * y_scale)
            
            boxes.append([x_min, y_min, x_max - x_min, y_max - y_min])
            scores.append(float(confidence))
            class_ids.append(class_id)

    # NMS 적용
    indices = cv2.dnn.NMSBoxes(boxes, scores, confidence_threshold, nms_threshold)

    # NMS 결과 바운딩 박스 그리기
    if len(indices) > 0:
        for i in indices.flatten():
            box = boxes[i]
            x, y, w, h = box
            draw_bounding_box(
                original_image,  # 원본 이미지에 바운딩 박스를 그리도록 변경
                class_ids[i],
                scores[i],
                x,
                y,
                x + w,
                y + h
            )

    # 이미지 RGB -> BGR 변환 후 저장
    output_image = cv2.cvtColor(original_image, cv2.COLOR_RGB2BGR)
    cv2.imwrite(output_path, output_image)
    print(f"추론 완료, 바운딩 박스가 그려진 이미지가 {output_path}에 저장되었습니다.")

if __name__ == "__main__":
    main()
