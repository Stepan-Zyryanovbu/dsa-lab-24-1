import random
import threading
import time
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)


@app.route('/number/', methods=['GET'])
def get_number():
    try:
        param = float(request.args.get('param', 1))
        result = random.uniform(1, 100) * param
        return jsonify({"result": result}), 200
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid param"}), 400


@app.route('/number/', methods=['POST'])
def post_number():
    try:
        data = request.get_json()
        json_param = float(data.get('jsonParam', 1))
        random_value = random.uniform(1, 100)
        operation = random.choice(['+', '-', '*', '/'])
        result = {
            "value": random_value * json_param,
            "operation": operation
        }
        return jsonify(result), 200
    except (TypeError, ValueError, AttributeError):
        return jsonify({"error": "Invalid JSON data"}), 400


@app.route('/number/', methods=['DELETE'])
def delete_number():
    random_value = random.uniform(1, 100)
    operation = random.choice(['+', '-', '*', '/'])
    result = {
        "value": random_value,
        "operation": operation
    }
    return jsonify(result), 200


def run_server():
    app.run(debug=False, port=5000)


def main():
     while True:
        time.sleep(100)

if __name__ == '__main__':
    # Запускаем сервер в отдельном потоке
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()


    main()