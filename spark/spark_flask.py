import os
import subprocess
import tempfile
import uuid
import csv

import io
import zipfile

from flask import Flask, request, send_file
from flask_cors import CORS, cross_origin

import pyarrow as pa

app = Flask(__name__)

cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

def download_and_zip_hdfs_folder(hdfs_folder_path, local_zip_path):
    # Connect to HDFS
    hdfs_conn = pa.hdfs.connect()
    
    # Create a temporary directory to store the folder's contents
    with tempfile.TemporaryDirectory() as tmpdirname:
        # List all files in the HDFS folder
        files = hdfs_conn.ls(hdfs_folder_path)
        
        for file_path in files:
            # Define the local path for the file
            local_file_path = os.path.join(tmpdirname, os.path.basename(file_path))
            # Download the file
            hdfs_conn.download(file_path, local_file_path)
        
        # Zip the contents of the temporary directory
        with zipfile.ZipFile(local_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(tmpdirname):
                for file in files:
                    file_path = os.path.join(root, file)
                    zipf.write(file_path, arcname=os.path.relpath(file_path, tmpdirname))


@app.route("/process", methods=["POST"])
@cross_origin()
def process():
    hdfs_connect  = pa.hdfs.connect()
    print(request.files)

    file_data = {}

    for filename, file in request.files.items():
        file_data[filename] = file

    uuidStr = str(uuid.uuid4())
    newpath = f"hdfs://192.168.68.67:54310/{uuidStr}"
    if not hdfs_connect.exists(newpath):
        hdfs_connect.mkdir(newpath)

    index = 0

    hdfs_file_paths = []

    # Upload images to hdfs
    for filename, file  in file_data.items():
        if file.filename == '':
            continue 

        hdfs_file_path = f"hdfs://192.168.68.67:54310/{uuidStr}/{filename}"
        with hdfs_connect.open(hdfs_file_path, 'wb') as hdfs_file:
            # Stream the file from the request to HDFS in chunks
            chunk_size = 4096  # Define the chunk size (4 KB in this example)
            while True:
                chunk = file.stream.read(chunk_size)
                if not chunk:
                    break
                hdfs_file.write(chunk)

        hdfs_file_paths.append(hdfs_file_path)
        index += 1

    # Write csv to a in-memory bytes buffer
    csv_buffer = io.BytesIO()
    text_buffer = io.TextIOWrapper(csv_buffer, encoding='utf-8', write_through=True)
    writer = csv.writer(text_buffer)
    for file_path in hdfs_file_paths:
        writer.writerow([file_path])

    # Seek to the begining
    csv_buffer.seek(0)

    # Upload the temporary file to HDFS
    csv_hdfs_path = f'hdfs://192.168.68.67:54310/{uuidStr}.csv'
    with hdfs_connect.open(csv_hdfs_path, 'wb') as csvfile:
        csvfile.write(csv_buffer.read())

    print(f"csv_hdfs_path: {csv_hdfs_path}")
    result = subprocess.run(['./submit.sh', csv_hdfs_path], 
                            stdout=subprocess.PIPE, 
                            stderr=subprocess.PIPE, 
                            text=True,
                            cwd=os.path.join(app.root_path)
                            )
    # Check the output
    if result.returncode == 0:
        print("Script executed successfully.")
        
        result_hdfs_path = f"{csv_hdfs_path}.result.parquet"
        result_local_path = os.path.join(app.root_path, f'{uuidStr}.result.zip')
        download_and_zip_hdfs_folder(result_hdfs_path, result_local_path)

        # Send the file to the client
        return send_file(result_local_path, as_attachment=True, download_name='result.parquet.zip')

    else:
        print("Script execution failed.")
        print(result.stderr)
        return result.stderr 

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001)
