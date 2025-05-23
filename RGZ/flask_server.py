from flask import Flask, request, jsonify

app = Flask(__name__)

RATES = {
    "USD": 90.50,
    "EUR": 98.30
}

@app.route("/rate")
def get_rate():
    try:
        currency = request.args.get("currency")
        if currency not in RATES:
            return jsonify({"message": "UNKNOWN CURRENCY"}), 400
        return jsonify({"rate": RATES[currency]}), 200
    except Exception:
        return jsonify({"message": "UNEXPECTED ERROR"}), 500

if __name__ == "__main__":
    app.run(port=5000)
