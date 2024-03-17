from flask import Flask, request

app = Flask(__name__)

@app.route("/process", methods=["POST"])
def process():
    print("REQUEST RECEIVED HERE")

    files = request.files
    print(files)
    return "Image received"
    


# Run the Flask app
if __name__ == "__main__":
    app.run(port=5002)
