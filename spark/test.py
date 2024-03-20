import os
import csv
import uuid

from flask import Flask, request
from flask_cors import CORS, cross_origin

app = Flask(__name__)

cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

@app.route("/process", methods=["POST"])
@cross_origin()
def process():

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

    return "Files saved"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001)