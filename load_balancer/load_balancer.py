from flask import Flask, request
import requests

app = Flask(__name__)

spark_nodes = ["http://127.0.0.1:5001/"]
current_node_index = 0

def get_next_server():
    global current_node_index
    current_node = spark_nodes[current_node_index]
    current_node_index = (current_node_index + 1) % len(spark_nodes)
    return current_node

@app.route('/upload', methods=['POST'])
def upload_image():
    print(request.files)
    print("REQUEST RECEIVED HERE")
    files = request.files
    
    optimal_node = get_next_server()

    response = requests.post(f"{optimal_node}/process", files=files)
    
    return response.text

if __name__ == '__main__':
    app.run(port=5000)
