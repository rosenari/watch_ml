import tritonclient.http as httpclient
import numpy as np
import cv2

# triton - client 테스트

# 클래스 이름 설정
CLASSES = ['car']
colors = np.random.uniform(0, 255, size=(len(CLASSES), 3))

def draw_bounding_box(img, class_id, confidence, x, y, x_plus_w, y_plus_h):
    label = f"{CLASSES[class_id]} ({confidence:.2f})"
    color = colors[class_id]
    cv2.rectangle(img, (int(x), int(y)), (int(x_plus_w), int(y_plus_h)), color, 2)
    cv2.putText(img, label, (int(x), int(y) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

def main():
    # Triton 서버 설정
    triton_url = "localhost:8000"
    model_name = "example_model"
    input_name = "images"
    output_name = "output0"

    # 이미지 경로
    image_path = "./mock/input_image.jpg"

    # 입력 이미지 읽기
    original_image = cv2.imread(image_path)
    if original_image is None:
        print(f"Error: Could not read image {image_path}")
        return

    # 이미지의 높이와 너비 가져오기
    height, width = original_image.shape[:2]

    # 입력 이미지를 정사각형으로 만들기 (패딩)
    length = max(height, width)
    image = np.zeros((length, length, 3), dtype=np.uint8)
    image[0:height, 0:width] = original_image

    # 스케일 계산
    scale = length / 640

    # 이미지 전처리 (OpenCV 코드와 동일하게)
    blob = cv2.dnn.blobFromImage(image, scalefactor=1 / 255.0, size=(640, 640), swapRB=True, crop=False)

    # Triton 클라이언트 생성
    triton_client = httpclient.InferenceServerClient(url=triton_url)

    # 입력 데이터 설정
    inputs = []
    inputs.append(httpclient.InferInput(input_name, blob.shape, "FP32"))
    inputs[0].set_data_from_numpy(blob)

    # 출력 데이터 설정
    outputs = []
    outputs.append(httpclient.InferRequestedOutput(output_name))

    # 추론 실행
    response = triton_client.infer(
        model_name=model_name,
        inputs=inputs,
        outputs=outputs
    )

    # 출력 데이터 추출
    output_data = response.as_numpy(output_name)

    # 출력 텐서 처리 (OpenCV 코드와 동일하게)
    outputs = np.array([cv2.transpose(output_data[0])])
    rows = outputs.shape[1]

    boxes = []
    scores = []
    class_ids = []

    # 신뢰도 및 NMS 임계값 설정
    confidence_threshold = 0.5
    nms_threshold = 0.45

    # 각 예측 결과를 순회하면서 처리
    for i in range(rows):
        classes_scores = outputs[0][i][4:]
        _, confidence, _, maxLoc = cv2.minMaxLoc(classes_scores)
        class_id = maxLoc[0]
        if confidence >= confidence_threshold:
            # 바운딩 박스 좌표 계산
            x = outputs[0][i][0]
            y = outputs[0][i][1]
            w = outputs[0][i][2]
            h = outputs[0][i][3]

            box = [
                x - 0.5 * w,
                y - 0.5 * h,
                w,
                h
            ]
            boxes.append(box)
            scores.append(float(confidence))
            class_ids.append(class_id)

    # NMS 적용
    indices = cv2.dnn.NMSBoxes(boxes, scores, confidence_threshold, nms_threshold)

    # 바운딩 박스 그리기
    if len(indices) > 0:
        for i in indices.flatten():
            box = boxes[i]
            x = box[0] * scale
            y = box[1] * scale
            w = box[2] * scale
            h = box[3] * scale
            x_plus_w = x + w
            y_plus_h = y + h

            draw_bounding_box(
                original_image,
                class_ids[i],
                scores[i],
                x,
                y,
                x_plus_w,
                y_plus_h
            )

    # 결과 이미지 표시
    cv2.imshow("Detection", original_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
