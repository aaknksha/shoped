import os
import sqlite3
from datetime import datetime
from flask import Flask, jsonify, render_template, request, session

app = Flask(__name__)
app.secret_key = os.environ.get("APP_SECRET", "shopease-student-demo-secret")
DB_PATH = os.environ.get("DB_PATH", "shopease.db")

SEED_PRODUCTS = [
    (1, "Classic White Sneakers", "Footwear", 1499, "Clean everyday sneakers for casual outfits.", "👟"),
    (2, "Everyday Backpack", "Accessories", 899, "A lightweight backpack for college and travel.", "🎒"),
    (3, "Minimal Wrist Watch", "Accessories", 1299, "A simple watch with a clean everyday look.", "⌚"),
    (4, "Cotton Casual T-Shirt", "Clothing", 499, "A comfortable cotton tee for daily wear.", "👕"),
    (5, "Wireless Headphones", "Electronics", 1799, "Enjoy music while studying or travelling.", "🎧"),
    (6, "Steel Water Bottle", "Lifestyle", 349, "Reusable bottle for everyday hydration.", "🧴"),
]

def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    folder = os.path.dirname(DB_PATH)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with connect_db() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY, name TEXT NOT NULL, category TEXT NOT NULL,
            price INTEGER NOT NULL, description TEXT NOT NULL, emoji TEXT NOT NULL)""")
        db.execute("""CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT, customer_name TEXT NOT NULL,
            items_json TEXT NOT NULL, total INTEGER NOT NULL, created_at TEXT NOT NULL)""")
        count = db.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        if count == 0:
            db.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?, ?)", SEED_PRODUCTS)

@app.route("/")
def home():
    return render_template("index.html", architecture="Monolithic")

@app.get("/api/products")
def products():
    with connect_db() as db:
        rows = db.execute("SELECT * FROM products ORDER BY id").fetchall()
    return jsonify([dict(row) for row in rows])

@app.get("/api/cart")
def get_cart():
    cart = session.get("cart", {})
    with connect_db() as db:
        result, total = [], 0
        for product_id, quantity in cart.items():
            product = db.execute("SELECT * FROM products WHERE id = ?", (int(product_id),)).fetchone()
            if product:
                item_total = product["price"] * int(quantity)
                result.append({"product": dict(product), "quantity": int(quantity), "subtotal": item_total})
                total += item_total
    return jsonify({"items": result, "total": total})

@app.post("/api/cart")
def update_cart():
    data = request.get_json(silent=True) or {}
    product_id = str(data.get("product_id", ""))
    try:
        quantity = int(data.get("quantity", 1))
    except (ValueError, TypeError):
        return jsonify({"error": "Quantity must be a number."}), 400
    if quantity < 0 or quantity > 99:
        return jsonify({"error": "Quantity must be between 0 and 99."}), 400
    with connect_db() as db:
        product = db.execute("SELECT id FROM products WHERE id = ?", (product_id,)).fetchone()
    if not product:
        return jsonify({"error": "Product not found."}), 404
    cart = session.get("cart", {})
    if data.get("add") and quantity > 0:
        quantity = int(cart.get(product_id, 0)) + quantity
    if quantity > 99:
        return jsonify({"error": "Maximum quantity per product is 99."}), 400
    if quantity == 0:
        cart.pop(product_id, None)
    else:
        cart[product_id] = quantity
    session["cart"] = cart
    return get_cart()

@app.post("/api/checkout")
def checkout():
    data = request.get_json(silent=True) or {}
    customer_name = str(data.get("customer_name", "")).strip()
    if not customer_name:
        return jsonify({"error": "Please enter your name."}), 400
    cart = session.get("cart", {})
    if not cart:
        return jsonify({"error": "Your cart is empty."}), 400
    with connect_db() as db:
        items, total = [], 0
        for product_id, quantity in cart.items():
            product = db.execute("SELECT * FROM products WHERE id = ?", (int(product_id),)).fetchone()
            if product:
                subtotal = product["price"] * int(quantity)
                items.append({"name": product["name"], "quantity": int(quantity), "subtotal": subtotal})
                total += subtotal
        if not items:
            return jsonify({"error": "No valid products in cart."}), 400
        cursor = db.execute("INSERT INTO orders (customer_name, items_json, total, created_at) VALUES (?, ?, ?, ?)",
                            (customer_name, __import__("json").dumps(items), total, datetime.now().isoformat(timespec="seconds")))
        order_id = cursor.lastrowid
    session["cart"] = {}
    return jsonify({"message": "Order placed successfully!", "order_id": order_id, "total": total}), 201

@app.get("/api/orders")
def orders():
    with connect_db() as db:
        rows = db.execute("SELECT id, customer_name, items_json, total, created_at FROM orders ORDER BY id DESC LIMIT 20").fetchall()
    import json
    return jsonify([{"id": r["id"], "customer_name": r["customer_name"], "items": json.loads(r["items_json"]),
                     "total": r["total"], "created_at": r["created_at"]} for r in rows])

init_db()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
