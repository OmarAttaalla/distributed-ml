from flask import Flask, request
from flask_cors import CORS, cross_origin

import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, pandas_udf
from pyspark.sql.types import StringType
import torch

import uuid
import os
import csv
from subprocess import Popen, PIPE

from models.common import DetectMultiBackend
from utils.general import (non_max_suppression, scale_boxes, xyxy2xywh)
from utils.torch_utils import select_device

app = Flask(__name__)

cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

spark = SparkSession.builder.appName("YOLOv9Inference").getOrCreate()

weights: str = '/yolov9-c.pt'
conf_thres: float = 0.25
iou_thres: float = 0.45
max_det: int = 1000
device: str = 'cpu'

@pandas_udf(StringType())
def yolov9_inference_udf(image_data_set: pd.Series) -> pd.Series:
    device = select_device(device)
    model = DetectMultiBackend(weights, device=device)
    stride = model.stride
    names = model.names

    results = {}

    for image_data in image_data_set:
        img = torch.from_numpy(image_data).to(device)
        img = img.float()
        img /= 255.0 
        if len(img.shape) == 3:
            img = img.unsqueeze(0)

        pred = model(img)

        pred = non_max_suppression(pred, conf_thres, iou_thres, classes=None, agnostic=False, max_det=max_det)

        detectionResult = []
        for i, det in enumerate(pred):
            if len(det):
                det[:, :4] = scale_boxes(img.shape[2:], det[:, :4], img.shape[2:]).round()

                for *xyxy, conf, cls in reversed(det):
                    xywh = xyxy2xywh(torch.tensor(xyxy).view(1, 4)).view(-1).tolist()
                    label = f"{names[int(cls)]} {conf:.2f}"
                    detectionResult.append({"label": label, "bbox": xywh, "confidence": conf.item()})
        results[image_data] = detectionResult
    return pd.Series(results)

@app.route("/process", methods=["POST"])
@cross_origin()
def process():
    print(request.files)

    file_data = {}

    for filename, file in request.files.items():
        file_data[filename] = file

    newpath = os.path.join('.', str(uuid.uuid4()))
    if not os.path.exists(newpath):
        os.makedirs(newpath)

    index = 0

    file_paths = []

    for filename, file  in file_data.items():
        if file.filename == '':
            continue 

        file.save(os.path.join(newpath, str(file.filename)))
        print(filename, newpath)
        file_paths.append(os.path.join(newpath, file.filename))
        index += 1

    with open('file_names.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for file_path in file_paths:
            writer.writerow([file_path])

    put = Popen(["hadoop", "fs", "-put", 'file_names.csv', "hdfs://192.168.68.67:54310/data.csv"], stdin=PIPE, bufsize=-1)
    put.communicate()
    
    df = spark.read.csv('file_names.csv').select(col("_c0").alias("image_path"))

    results_df = df.withColumn("inference_results", yolov9_inference_udf(df["image_path"]))

    results_df.show()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001)
