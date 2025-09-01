from flask import Flask, request
import logging

app = Flask(__name__)

# Configure logging to stdout
logging.basicConfig(level=logging.INFO)

@app.route("/", methods=["GET", "POST"])
def home():
    logging.info("Incoming request: %s %s", request.method, request.path)
    logging.info("Headers: %s", dict(request.headers))
    if request.method == "POST":
        logging.info("Payload: %s", request.get_data(as_text=True))
    return {"message": "Hello from Flask!"}, 200

if __name__ == "__main__":
    # Host must be 0.0.0.0 so Docker can listen externally
    app.run(host="0.0.0.0", port=5000)
