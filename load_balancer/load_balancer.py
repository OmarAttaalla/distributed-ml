from flask import Flask, request
import requests
import os
from flask_cors import CORS, cross_origin
from werkzeug.datastructures import FileStorage


app = Flask(__name__)

cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

spark_nodes = ["http://68.5.202.220:48027/, http://68.5.202.220:48027/"]
current_node_index = 0

#current load on each node
node_loads = [0, 0]

def get_next_round_robin():
    global current_node_index
    current_node = spark_nodes[current_node_index]
    print(f"Sending to Master Node {current_node_index}")
    current_node_index = (current_node_index + 1) % len(spark_nodes)
    return current_node

#uses size of incoming request to determine which server to send to next
def get_least_load_first(files):
    min_load = -1
    min_index = 0

    for i in range(len(node_loads)):
        print(f"Node {i} load: {node_loads[i]}")
        if node_loads[i] < min_load or min_load == -1:
            min_load = node_loads[i]
            min_index = i

    print(f"Min load: {min_load} at node {min_index}")

    #reduce loads by min load to avoid overflow
    for i in range(len(node_loads)):
        node_loads[i] = node_loads[i] - min_load
    
    request_size = 0

    files = list(files)

    for file in files[0]:
        blob = file.read()
        print(len(blob))
        request_size += len(blob)
        file.seek(0, os.SEEK_SET)

    node_loads[min_index] += request_size

    print(f"Sending to Master Node {min_index}")

    return spark_nodes[min_index]


@app.route('/upload', methods=['POST'])
@cross_origin()
def upload_image():
    files = request.files.listvalues()
    
    optimal_node = get_least_load_first(files)

    print(request.files)

    response = requests.post(f"{optimal_node}/process", files=request.files)
    
    return response.text

if __name__ == '__main__':
    app.run(port=5000)
