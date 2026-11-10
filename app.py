from flask import Flask, render_template, jsonify
from gpu import get_gpu, get_processes

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/gpu")
def api_gpu():
    return jsonify(get_gpu())


@app.route("/api/processes")
def api_processes():
    return jsonify(get_processes())


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
