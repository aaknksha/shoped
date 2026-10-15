import os
import requests
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
PRODUCT_URL = os.environ.get("PRODUCT_SERVICE_URL", "http://localhost:5001")
CART_URL = os.environ.get("CART_SERVICE_URL", "http://localhost:5003")
ORDER_URL = os.environ.get("ORDER_SERVICE_URL", "http://localhost:5004")
TIMEOUT = 5

@app.route("/")
def home():
    return render_template("index.html", architecture="Microservices")

def forward(url, method="GET", payload=None):
    try:
        response = requests.request(method, url, json=payload, timeout=TIMEOUT)
        try:
            data = response.json()
        except ValueError:
            data = {"error": "Service returned an invalid response."}
        return jsonify(data), response.status_code
    except requests.RequestException:
        return jsonify({"error": "A backend service is unavailable. Check Docker Compose logs."}), 503

@app.get("/api/products")
def products():
    return forward(f"{PRODUCT_URL}/products")

@app.get("/api/cart")
def get_cart():
    return forward(f"{CART_URL}/cart")

@app.post("/api/cart")
def update_cart():
    return forward(f"{CART_URL}/cart", "POST", request.get_json(silent=True) or {})

@app.post("/api/checkout")
def checkout():
    return forward(f"{ORDER_URL}/checkout", "POST", request.get_json(silent=True) or {})

@app.get("/api/orders")
def orders():
    return forward(f"{ORDER_URL}/orders")

@app.get("/health")
def health():
    return {"status": "ok", "service": "gateway"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
