from flask import Flask, request
import requests
import os

app = Flask(__name__)

spark_nodes = ["http://127.0.0.1:5001/", "http://127.0.0.1:5002/"]
current_node_index = 0

#current load on each node
node_loads = [0, 0]

def get_next_round_robin():
    global current_node_index
    current_node = spark_nodes[current_node_index]
    current_node_index = (current_node_index + 1) % len(spark_nodes)
    return current_node

#uses size of incoming request to determine which server to send to next
def get_next_weighted_round_robin(files):
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

    node_loads[min_index] += request_size

    return spark_nodes[min_index]


@app.route('/upload', methods=['POST'])
def upload_image():
    print(request.files)
    print("REQUEST RECEIVED HERE")
    files = request.files.listvalues()

    print(files)
    
    optimal_node = get_next_weighted_round_robin(files)

    print(optimal_node)

    print(f"Sending to {optimal_node}")

    response = requests.post(f"{optimal_node}/process", files=request.files)
    
    return response.text

if __name__ == '__main__':
    app.run(port=5000)
