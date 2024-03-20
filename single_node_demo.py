from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import torch
import cv2
import numpy as np
import json
import os

import uuid

from tqdm import tqdm
from models.common import DetectMultiBackend
from utils.augmentations import letterbox
from utils.general import (non_max_suppression, scale_boxes, xyxy2xywh)
from utils.torch_utils import select_device

# Path to weights file
weights = './yolov9-c.pt'
conf_thres: float = 0.25
iou_thres: float = 0.45
max_det: int = 1000

import numpy as np

app = Flask(__name__)

cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

weights: str = '../yolov9-c.pt'
conf_thres: float = 0.25
iou_thres: float = 0.45
max_det: int = 1000
device: str = 'cpu'

def yolov9_inference(image_directory):
    device = select_device("cpu")
    model = DetectMultiBackend(weights, device=device)
    stride = model.stride
    names = model.names

    results = {}
    folder_items = os.listdir(image_directory)
    pbar = tqdm(total=len(folder_items))

    for image_path in folder_items:
        pbar.update(1)

        img = cv2.imread(os.path.join(image_directory, image_path), cv2.IMREAD_COLOR)

        # Process image_data to match YOLOv9 input requirements
        img = letterbox(img, stride=stride, auto=True)[0]  # padded resize
        img = img.transpose((2, 0, 1))[::-1]  # HWC to CHW, BGR to RGB
        img = np.ascontiguousarray(img)  # contiguous
        img = torch.from_numpy(img).to(device)
        img = img.float()  # Convert to float
        img /= 255.0  # Scale image to [0, 1]
        if len(img.shape) == 3:
            img = img.unsqueeze(0)  # Add batch dimension

        # Inference
        pred = model(img)

        # Apply Non-Max Suppression
        pred = non_max_suppression(pred, conf_thres, iou_thres, classes=None, agnostic=False, max_det=max_det)

        # Process predictions (example: extract and return bounding boxes and classes)
        detectionResult = []
        for i, det in enumerate(pred):  # For each image in batch (batch size is 1 here)
            if len(det):
                # Convert detections to xywh format
                det[:, :4] = scale_boxes(img.shape[2:], det[:, :4], img.shape[2:]).round()

                for *xyxy, conf, cls in reversed(det):
                    xywh = xyxy2xywh(torch.tensor(xyxy).view(1, 4)).view(-1).tolist()
                    label = f"{names[int(cls)]} {conf:.2f}"
                    detectionResult.append({"label": label, "bbox": xywh, "confidence": conf.item()})
        results[image_path] = detectionResult
    
    with open('./result.json', 'w') as f:
        f.write(json.dumps(results))
    
    return results

@app.route("/process", methods=["POST"])
@cross_origin()
def process():
    print(request.files)

    file_data = {}

    for filename, file in request.files.items():
        file_data[filename] = file

    print(file_data)

    newpath = os.path.join('.', str(uuid.uuid4()))
    if not os.path.exists(newpath):
        os.makedirs(newpath)

    index = 0

    for filename, file  in file_data.items():
        if file.filename == '':
            continue 

        file.save(os.path.join(newpath, str(filename)))
        index += 1

    # Perform inference
    inference_results = yolov9_inference(newpath)

    return inference_results


if __name__ == "__main__":
    app.run(port=5001)
