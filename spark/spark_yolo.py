import argparse

import json
import numpy as np
import pandas as pd
import pyarrow as pa
from pyspark import SparkFiles
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, pandas_udf
from pyspark.sql.types import StringType
import torch
import cv2

from models.common import DetectMultiBackend
from utils.augmentations import letterbox
from utils.general import (non_max_suppression, scale_boxes, xyxy2xywh)
from utils.torch_utils import select_device

# Initialize Spark Session
spark = SparkSession.builder.appName("Spark-YOLOv9").getOrCreate()

conf_thres: float = 0.25
iou_thres: float = 0.45
max_det: int = 1000

@pandas_udf(StringType())
def yolov9_inference_udf(image_data_set: pd.Series) -> pd.Series:
    """
    Run YOLOv9 inference on a single image.

    Parameters:
    - weights: Path to the YOLOv9 weights file.
    - conf_thres: Confidence threshold for detections.
    - iou_thres: IOU threshold for non-max suppression.
    - max_det: Maximum number of detections per image.

    Returns:
    - Inference results in a structured format.
    """

    hdfs_connect  = pa.hdfs.connect()

    # Initialize model and device
    device = select_device("cpu")
    model = DetectMultiBackend(SparkFiles.get('yolov9-c.pt'), device=device)
    stride = model.stride
    names = model.names

    results = {}

    for image_path in image_data_set:
        # Use PyArrow to read image data from HDFS
        with hdfs_connect.open(image_path, 'rb') as f:
            image_data = f.read()

        img_array = np.frombuffer(image_data, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

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
        results[image_path] = json.dumps(detectionResult)
    # Convert the results dictionary to a Pandas Series before returning
    # The Series index will be the image paths, and the values will be the serialized JSON strings of detection results
    return pd.Series([results[image_path] for image_path in image_data_set], index=image_data_set)

parser = argparse.ArgumentParser()
parser.add_argument("--csv", help="Url to the csv file on hdfs", required=True)
args = parser.parse_args()

# Read DataFrame with image paths from csv
print(f"csv url: {args.csv}")
df = spark.read.csv(args.csv).select(col("_c0").alias("image_path"))

results_df = df.withColumn("inference_results", yolov9_inference_udf(df["image_path"]))

# Show results
# results_df.show()

# Write result to hdfs
results_df.write.parquet(f'{args.csv}.result.parquet')