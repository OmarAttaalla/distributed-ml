#!/bin/bash

spark-submit \
    --master yarn \
    --archives pyspark_venv.tar.gz#environment \
    --deploy-mode cluster \
    --files yolov9-c.pt \
    --conf spark.yarn.appMasterEnv.PYSPARK_PYTHON=./environment/bin/python \
    spark_yolo.py --csv $1