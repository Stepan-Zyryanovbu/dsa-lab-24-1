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
    base_url = 'http://127.0.0.1:5000/number/'

    # 1. GET запрос
    param_value = random.randint(1, 10)
    response_get = requests.get(base_url, params={'param': param_value})
    get_data = response_get.json()
    value_1 = get_data['result']
    operation_1 = '*'  # GET всегда умножает

    # 2. POST запрос
    json_value = random.randint(1, 10)
    headers = {'Content-Type': 'application/json'}
    response_post = requests.post(
        base_url,
        json={"jsonParam": json_value},
        headers=headers
    )
    post_data = response_post.json()
    value_2 = post_data['value']
    operation_2 = post_data['operation']

    # 3. DELETE запрос
    response_delete = requests.delete(base_url)
    delete_data = response_delete.json()
    value_3 = delete_data['value']
    operation_3 = delete_data['operation']

    # 4. Вычисление итогового выражения
    expression = f"(({value_1} {operation_2} {value_2}) {operation_3} {value_3})"
    result = int(eval(expression))

    print(f"GET: {value_1:.2f} * {param_value}")
    print(f"POST: {value_2:.2f} {operation_2}")
    print(f"DELETE: {value_3:.2f} {operation_3}")
    print(f"Expression: {expression}")
    print(f"Final Result (int): {result}")


if __name__ == '__main__':
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()

    main()
    while True:
        time.sleep(1)