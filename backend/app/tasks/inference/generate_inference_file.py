import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def generate_inference_file(file_type: str, original_file_path: str, model_name: str, classes: list[str]) -> str:
    """Inference 파일 생성 (이미지 또는 비디오)"""
    # 필요한 모듈을 함수 내에서 로드
    import numpy as np
    import cv2
    import tritonclient.grpc as grpcclient
    from tritonclient.grpc import InferInput, InferRequestedOutput
    from app.config import TRITON_GRPC_URL, INFERENCE_DIRECTORY

    confidence_threshold = 0.3
    nms_threshold = 0.4
    output_dir = INFERENCE_DIRECTORY
    output_path = os.path.join(output_dir, f"detection_{os.path.basename(original_file_path)}")
    triton_client = grpcclient.InferenceServerClient(url=TRITON_GRPC_URL)

    def _generate_primary_colors(num_colors):
        """기본 원색 계열 색상 생성"""
        primary_colors = [
            (255, 0, 0), (0, 255, 0), (0, 0, 255),
            (255, 255, 0), (255, 0, 255), (0, 255, 255)
        ]
        colors = []
        np.random.seed(0)
        for i in range(num_colors):
            base_color = primary_colors[i % len(primary_colors)]
            variation = np.random.randint(0, 50, size=3)
            color = tuple(max(0, min(255, base + var)) for base, var in zip(base_color, variation))
            colors.append(tuple(map(int, color)))
        return colors
    
    def _draw_bounding_box(img, class_id, confidence, x, y, x_plus_w, y_plus_h, colors):
        """Bounding Box 그리기"""
        label = f"{classes[class_id]} ({confidence:.2f})"
        color = colors[class_id % len(colors)]
        cv2.rectangle(img, (int(x), int(y)), (int(x_plus_w), int(y_plus_h)), color, 2)
        cv2.putText(img, label, (int(x), int(y) - 10), cv2.FONT_HERSHEY_PLAIN, 1.8, color, 2)

    def _infer_bounding_boxes(triton_client, model_name, image, original_dims):
        """Triton 추론 및 bounding box 생성"""
        inputs = [InferInput("images", image.shape, "FP32")]
        inputs[0].set_data_from_numpy(image)
        outputs = [InferRequestedOutput("output0")]
        response = triton_client.infer(model_name=model_name, inputs=inputs, outputs=outputs)
        output_data = response.as_numpy("output0")[0]

        boxes, scores, class_ids = [], [], []
        x_scale, y_scale = original_dims[1] / 640, original_dims[0] / 640

        for detection in output_data:
            x_min, y_min, x_max, y_max, confidence, class_id = detection[:6]
            if confidence >= confidence_threshold:
                x_min, y_min = int(x_min * x_scale), int(y_min * y_scale)
                x_max, y_max = int(x_max * x_scale), int(y_max * y_scale)
                boxes.append([x_min, y_min, x_max - x_min, y_max - y_min])
                scores.append(float(confidence))
                class_ids.append(int(class_id))

        indices = cv2.dnn.NMSBoxes(boxes, scores, confidence_threshold, nms_threshold)
        return [(boxes[i], scores[i], class_ids[i]) for i in indices.flatten()]
    
    def _process_frame(triton_client, model_name, frame, colors):
        """개별 비디오 프레임을 처리"""
        original_dims = frame.shape[:2]
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        processed_image = cv2.resize(frame_rgb, (640, 640)).astype(np.float32) / 255.0
        processed_image = np.transpose(processed_image, (2, 0, 1))
        processed_image = np.expand_dims(processed_image, axis=0)

        detections = _infer_bounding_boxes(triton_client, model_name, processed_image, original_dims)
        for (box, score, class_id) in detections:
            x, y, w, h = box
            _draw_bounding_box(frame_rgb, class_id, score, x, y, x + w, y + h, colors)

        return cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    colors = _generate_primary_colors(len(classes))

    if file_type == 'photo':
        # 사진에 대한 추론 로직
        original_image = cv2.imread(original_file_path)
        if original_image is None:
            raise ValueError(f"Error: Could not read image {original_file_path}")
        original_image = cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB)

        original_dims = original_image.shape[:2]
        processed_image = cv2.resize(original_image, (640, 640)).astype(np.float32) / 255.0
        processed_image = np.transpose(processed_image, (2, 0, 1))
        processed_image = np.expand_dims(processed_image, axis=0)

        detections = _infer_bounding_boxes(triton_client, model_name, processed_image, original_dims)
        for (box, score, class_id) in detections:
            x, y, w, h = box
            _draw_bounding_box(original_image, class_id, score, x, y, x + w, y + h, colors)

        output_image = cv2.cvtColor(original_image, cv2.COLOR_RGB2BGR)
        cv2.imwrite(output_path, output_image)
        return output_path

    elif file_type == 'video':
        # 비디오에 대한 추론 로직
        cap = cv2.VideoCapture(original_file_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            processed_frame = _process_frame(triton_client, model_name, frame, colors)
            out.write(processed_frame)

        cap.release()
        out.release()
        return output_path

    else:
        raise ValueError(f"Unsupported file type: {file_type}")
